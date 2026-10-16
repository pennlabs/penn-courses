"""
Make saved courses agree with the schedule that is about to be drawn.

Claims are rebuilt on every generate. Two spellings of one cross-listed class
collapse to the earlier row. Mutually exclusive pairs are reported, not removed.
"""

from __future__ import annotations

import json
from pathlib import Path

from degree.models import Fulfillment
from degree.utils.degree_logic import prewarm_canonical_cache

_PAIRS: dict[str, list[str]] | None = None


def exclusive_partners() -> dict[str, list[str]]:
    global _PAIRS
    if _PAIRS is None:
        path = Path(__file__).resolve().parents[2] / "data" / "exclusive_pairs.json"
        try:
            _PAIRS = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            _PAIRS = {}
    return _PAIRS


def collapse_cross_listings(degree_plan):
    """Drop a later fulfillment that is another spelling of a course already kept."""
    rows = list(Fulfillment.objects.filter(degree_plan=degree_plan).order_by("semester", "full_code"))
    canonicals = prewarm_canonical_cache([row.full_code for row in rows])
    groups: dict[str, list] = {}
    for row in rows:
        groups.setdefault(canonicals.get(row.full_code, row.full_code), []).append(row)
    removed = []
    for members in groups.values():
        if len(members) < 2:
            continue
        keeper = members[0]
        for extra in members[1:]:
            removed.append(
                {
                    "full_code": extra.full_code,
                    "kind": "also_offered",
                    "components": [keeper.full_code],
                    "message": (
                        f"{extra.full_code.replace('-', ' ')} and "
                        f"{keeper.full_code.replace('-', ' ')} are the same course. "
                        f"{extra.full_code.replace('-', ' ')} was removed."
                    ),
                }
            )
            extra.delete()
    return removed


def mutex_violations(degree_plan):
    """Warn when both sides of a catalog exclusive pair are on the plan."""
    codes = list(
        Fulfillment.objects.filter(degree_plan=degree_plan).values_list("full_code", flat=True)
    )
    present = set(codes)
    partners = exclusive_partners()
    seen = set()
    violations = []
    for code in codes:
        for other in partners.get(code, []):
            if other not in present or other == code:
                continue
            pair = tuple(sorted((code, other)))
            if pair in seen:
                continue
            seen.add(pair)
            violations.append(
                {
                    "full_code": code,
                    "kind": "mutually_exclusive",
                    "components": [other],
                    "message": (
                        f"{code.replace('-', ' ')} is mutually exclusive with "
                        f"{other.replace('-', ' ')}."
                    ),
                }
            )
    return violations


def _rule_snapshot(degree_plan):
    rows = Fulfillment.objects.filter(degree_plan=degree_plan).prefetch_related("rules")
    return {
        row.full_code: tuple(sorted(rule.id for rule in row.rules.all()))
        for row in rows
    }


def prepare_plan(degree_plan):
    """Collapse cross-lists, then reallocate every remaining course. Returns what changed."""
    removed = collapse_cross_listings(degree_plan)
    before = _rule_snapshot(degree_plan)
    from degree.views import update_fulfillments

    update_fulfillments(degree_plan)
    after = _rule_snapshot(degree_plan)
    return {
        "removed": removed,
        "claims_updated": bool(removed) or before != after,
    }
