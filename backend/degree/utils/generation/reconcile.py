"""
Make saved courses agree with the schedule that is about to be drawn.

Claims are rebuilt on every generate. Two spellings of one cross-listed class
collapse to the earlier row. Cross-listings come from `Course.primary_listing`.
"""

from __future__ import annotations

from degree.models import Fulfillment
from degree.utils.degree_logic import prewarm_canonical_cache


def _cross_listed_groups(degree_plan):
    """Fulfillments that are spellings of one course, earliest first. Singletons are skipped."""
    rows = list(
        Fulfillment.objects.filter(degree_plan=degree_plan).order_by("semester", "full_code")
    )
    canonicals = prewarm_canonical_cache([row.full_code for row in rows])
    groups: dict[str, list] = {}
    for row in rows:
        groups.setdefault(canonicals.get(row.full_code, row.full_code), []).append(row)
    return [members for members in groups.values() if len(members) > 1]


def _same_course(extra, keeper):
    return (
        f"{extra.full_code.replace('-', ' ')} and "
        f"{keeper.full_code.replace('-', ' ')} are the same course."
    )


def collapse_cross_listings(degree_plan):
    """Drop a later fulfillment that is another spelling of a course already kept."""
    removed = []
    for keeper, *extras in _cross_listed_groups(degree_plan):
        for extra in extras:
            removed.append(
                {
                    "full_code": extra.full_code,
                    "kind": "also_offered",
                    "components": [keeper.full_code],
                    "message": (
                        f"{_same_course(extra, keeper)} "
                        f"{extra.full_code.replace('-', ' ')} was removed."
                    ),
                }
            )
            extra.delete()
    return removed


def cross_listing_violations(degree_plan):
    """Warn when two spellings of one cross-listed course are both on the plan."""
    return [
        {
            "full_code": extra.full_code,
            "kind": "also_offered",
            "components": [keeper.full_code],
            "message": _same_course(extra, keeper),
        }
        for keeper, *extras in _cross_listed_groups(degree_plan)
        for extra in extras
    ]


def _rule_snapshot(degree_plan):
    rows = Fulfillment.objects.filter(degree_plan=degree_plan).prefetch_related("rules")
    return {row.full_code: tuple(sorted(rule.id for rule in row.rules.all())) for row in rows}


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
