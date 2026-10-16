"""
Pair two open slots, one on each program, when one course could fill both.

The card stays a slot. It does not pick a winner. Ordinary department electives
are left as two cards. Writing, attribute rules, and named lists of at most 40
courses can pair.
"""

from __future__ import annotations

from decimal import Decimal

from courses.models import Course
from courses.util import get_current_semester
from degree.utils.degree_logic import is_graduate
from degree.utils.generation.open_rules import listed_course_codes


def _cutoff_semester():
    current = get_current_semester()
    year = int(str(current)[:4]) - 3
    return f"{year}A"

MAX_LIST = 40
MAX_SHOW = 12


def _parts(rule):
    parts = {"courses": [], "depts": [], "attrs": [], "gte": None, "lte": None}
    try:
        parsed = rule.q_json
    except Exception:
        parsed = None
    if parsed:
        from degree.utils.generation.open_rules import _collect_schedule_parts

        _collect_schedule_parts(parsed, parts)
    return parts


def _eligible(rule):
    """writing, attribute, or a short named list. A department elective is not."""
    codes = listed_course_codes(rule)
    if codes is not None:
        if 1 < len(codes) <= MAX_LIST:
            return "listed", codes
        return None, []
    parts = _parts(rule)
    departments = [str(code).upper() for code in parts["depts"]]
    title = (getattr(rule, "title", None) or "").lower()
    writing = "WRIT" in departments or "writ" in title or "writing" in title
    if writing:
        return "writing", []
    if departments:
        return None, []
    if parts["attrs"]:
        return "attribute", []
    return None, []


def _matches(rule, codes):
    """Which of `codes` satisfy `rule`. One query."""
    try:
        query = rule.get_q_object()
    except Exception:
        return []
    if not query:
        return []
    found = Course.objects.filter(query, full_code__in=list(codes)).values_list(
        "full_code", flat=True
    )
    return list(dict.fromkeys(found))


def _both(left, right):
    """Up to MAX_SHOW courses that satisfy both rules."""
    try:
        left_q = left.get_q_object()
        right_q = right.get_q_object()
    except Exception:
        return []
    if not left_q or not right_q:
        return []
    rows = (
        Course.objects.filter(left_q & right_q, semester__gte=_cutoff_semester())
        .order_by("full_code")
        .distinct("full_code")
        .values_list("full_code", flat=True)[:MAX_SHOW]
    )
    return list(rows)


def _intersection(left, left_kind, left_codes, right, right_kind, right_codes):
    if left_kind == "listed" and right_kind == "listed":
        shared = [code for code in left_codes if code in set(right_codes)]
        return shared[:MAX_SHOW]
    if left_kind == "listed":
        return _matches(right, left_codes)[:MAX_SHOW]
    if right_kind == "listed":
        return _matches(left, right_codes)[:MAX_SHOW]
    return _both(left, right)


def pair_placeholders(ghosts, plan_rules, sharing):
    """Replace eligible pairs with one placeholder. Other ghosts are unchanged."""
    policy = plan_rules.composition.policy
    if not policy.cross_component_sharing:
        return ghosts
    rules = {rule.id: rule for rule in plan_rules.rule_to_component}
    components = plan_rules.rule_to_component

    eligible = []
    rest = []
    for ghost in ghosts:
        rule_ids = ghost.get("rules") or []
        if ghost.get("kind") != "placeholder" or len(rule_ids) != 1:
            rest.append(ghost)
            continue
        # Credit-gap electives belong to one degree. Pairing would spend them
        # on the other degree's requirement.
        if str(ghost.get("slot_ids", [""])[0]).startswith("slot:free:"):
            rest.append(ghost)
            continue
        rule = rules.get(rule_ids[0])
        component = components.get(rule) if rule is not None else None
        if rule is None or component is None or not component.counts_toward_degree_cap:
            rest.append(ghost)
            continue
        kind, codes = _eligible(rule)
        if kind is None:
            rest.append(ghost)
            continue
        eligible.append((ghost, rule, component, kind, codes))

    candidates = []
    for index, left in enumerate(eligible):
        for right in eligible[index + 1 :]:
            if left[2].key == right[2].key:
                continue
            if is_graduate(left[2]) and is_graduate(right[2]):
                continue
            shared = _intersection(left[1], left[3], left[4], right[1], right[3], right[4])
            if not shared:
                continue
            specificity = (left[3] != "listed") + (right[3] != "listed")
            candidates.append((specificity, -len(shared), left, right, shared))
    candidates.sort(key=lambda row: (row[0], row[1]))

    used = set()
    paired = []
    for _specificity, _width, left, right, shared in candidates:
        if left[0]["slot_ids"][0] in used or right[0]["slot_ids"][0] in used:
            continue
        crosses = is_graduate(left[2]) != is_graduate(right[2])
        left_cu = Decimal(str(left[0]["cu"]))
        right_cu = Decimal(str(right[0]["cu"]))
        cu = min(left_cu, right_cu)
        if crosses and not sharing.allows(cu):
            continue
        if crosses:
            sharing.take(cu)
        used.add(left[0]["slot_ids"][0])
        used.add(right[0]["slot_ids"][0])
        paired.append(_card(left[0], right[0], shared, cu))
        # The larger requirement keeps the credits this one course did not cover.
        for side, side_cu in ((left, left_cu), (right, right_cu)):
            leftover = side_cu - cu
            if leftover <= 0:
                continue
            remainder = dict(side[0])
            remainder["cu"] = float(leftover)
            remainder["slot_ids"] = [f"{side[0]['slot_ids'][0]}:rest"]
            paired.append(remainder)

    kept = [ghost for ghost, *_rest in eligible if ghost["slot_ids"][0] not in used]
    return rest + kept + paired


def _card(left, right, courses, cu):
    return {
        "slot_ids": [left["slot_ids"][0], right["slot_ids"][0]],
        "kind": "placeholder",
        "full_code": None,
        "fulfillment_id": None,
        "label": f"{left.get('label') or left.get('short_label')} + {right.get('label') or right.get('short_label')}",
        "short_label": f"{left.get('short_label') or left.get('label')} + {right.get('short_label') or right.get('label')}",
        "cu": float(cu),
        "rules": [left["rules"][0], right["rules"][0]],
        "rule_q": left.get("rule_q"),
        "alternatives": courses,
        "course_number": 10**9,
        "overlap": True,
    }
