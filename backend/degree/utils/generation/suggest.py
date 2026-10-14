"""
Turn open slots into course ghosts, placeholders, and placement proposals.

Course choice goes through `allocate_rules`, the same function the editor uses when a
student drops a course on the plan, so a suggestion cannot claim a sharing the editor
would reject.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Q

from courses.models import Course
from courses.util import get_current_semester
from degree.utils.degree_logic import (
    DEFAULT_COURSE_CREDITS,
    allocate_rules,
    map_rules_and_degrees,
    prewarm_belongs_cache,
    prewarm_credits_cache,
    sharing_from_fulfillments,
)
from degree.utils.generation.overlap import pair_placeholders
from degree.utils.generation.open_rules import (
    is_coverage_rule,
    open_slots,
    schedule_code,
    listed_course_codes,
    schedule_exception,
    slot_cus,
    sole_listed_code,
    unplaced_fulfillments,
)


ALTERNATIVE_LIMIT = 24
FREE_ELECTIVE_LABEL = "Free Elective"
# A course already in the degree may carry at most two general-education labels.
MAX_COVERAGE_PER_COURSE = 2
# Relations whose owner is a Degree. Majors and minors share the owner_id column shape
# but point at a different model, so they are not padded to a degree total.
_DEGREE_RELATIONS = frozenset({"degrees", "college", "degree-major"})


def _fill_key(slot):
    """Specific courses and writing before broad restrictions. Breadth and free electives last."""
    exception = schedule_exception(slot.rule) or ""
    if exception == "WH Business Breadth":
        return (3, slot.slot_id)
    if exception == "Free Elective":
        return (4, slot.slot_id)
    title = (slot.rule.title or "").lower()
    if slot.kind == "listed" or "writ" in title or "writing" in title:
        return (0, slot.slot_id)
    return (2, slot.slot_id)


def _cutoff_semester():
    current = get_current_semester()
    year = int(str(current)[:4]) - 3
    return f"{year}A"


def _latest_by_code(courses):
    latest = {}
    for course in courses:
        current = latest.get(course.full_code)
        if current is None or course.semester > current.semester:
            latest[course.full_code] = course
    return list(latest.values())


def _sort_key(course):
    quality = course.precompute_course_quality
    difficulty = course.precompute_difficulty
    return (
        quality is None,
        -(quality or 0),
        difficulty is None,
        difficulty or 0,
        course.full_code,
    )


def _candidates(rule, blocked_codes, blocked_listings):
    q = rule.get_q_object() or Q()
    courses = Course.objects.filter(q, semester__gte=_cutoff_semester()).select_related(
        "primary_listing"
    )
    latest = _latest_by_code(courses)
    kept = []
    for course in latest:
        listing_id = course.primary_listing_id or course.id
        if course.full_code in blocked_codes or listing_id in blocked_listings:
            continue
        kept.append(course)
    kept.sort(key=_sort_key)
    return kept


def _block(course, blocked_codes, blocked_listings):
    blocked_codes.add(course.full_code)
    if course.primary_listing_id:
        blocked_listings.add(course.primary_listing_id)


def _snapshot_sharing(sharing):
    return (
        sharing.used,
        sharing.program_shared_cu_used,
        {key: set(value) for key, value in sharing.claims.items()},
    )


def _restore_sharing(sharing, snapshot):
    sharing.used, sharing.program_shared_cu_used, claims = snapshot
    sharing.claims.clear()
    sharing.claims.update(claims)


def _credits(course, credits_cache):
    return credits_cache.get(course.full_code, course.credits or DEFAULT_COURSE_CREDITS)


def cover_slots_with_planned_courses(slots, fulfillments, plan_rules, degree_plan):
    """
    Drop one open slot per planned course that `allocate_rules` would actually claim.

    Matching the rule and being allowed to double count is not enough. The sharing
    cap can still refuse the claim. A refused claim leaves the requirement on the
    schedule, because the requirements panel still shows it open.
    """
    if not slots or not fulfillments:
        return slots
    codes = [fulfillment.full_code for fulfillment in fulfillments]
    credits_cache = prewarm_credits_cache(codes)
    belongs = prewarm_belongs_cache({slot.rule for slot in slots}, codes)
    sharing = sharing_from_fulfillments(fulfillments, plan_rules.rule_to_component, credits_cache)
    for fulfillment in fulfillments:
        claimed = sharing.claims.setdefault(fulfillment.full_code, set())
        for rule in fulfillment.rules.all():
            component = plan_rules.rule_to_component.get(rule)
            if component is not None and component.counts_toward_degree_cap:
                claimed.add(component.key)
    open_rule_ids = {slot.rule_id for slot in slots}
    satisfied = {rule for rule in plan_rules.rule_to_component if rule.id not in open_rule_ids}
    used = set()
    drop = set()
    # Named course lists before broad restrictions, so a taken course closes the specific rule.
    for slot in sorted(slots, key=lambda item: (item.kind != "listed", item.slot_id)):
        for fulfillment in fulfillments:
            if fulfillment.id in used:
                continue
            if any(rule.id == slot.rule_id for rule in fulfillment.rules.all()):
                continue
            snapshot = _snapshot_sharing(sharing)
            selected, _, _ = allocate_rules(
                fulfillment.full_code,
                plan_rules.rules_per_component,
                plan_rules.rule_to_component,
                plan_rules.double_counts,
                rule_selected=slot.rule,
                degree_plan=degree_plan,
                satisfied_rules=set(satisfied),
                belongs_cache=belongs,
                is_transfer=fulfillment.is_transfer_credit,
                graduate_sharing=sharing,
                credits_cache=credits_cache,
                policy=plan_rules.composition.policy,
            )
            listed = listed_course_codes(slot.rule) or []
            other_choices = [code for code in listed if code != fulfillment.full_code]
            # A list that still has another course stays a choice. A restriction
            # closes only when this course matches it and the cap allows the claim.
            if (
                slot.rule not in selected
                or not belongs.get((slot.rule.id, fulfillment.full_code))
                or (len(listed) >= 2 and other_choices)
            ):
                _restore_sharing(sharing, snapshot)
                continue
            used.add(fulfillment.id)
            drop.add(slot.slot_id)
            break
    return [slot for slot in slots if slot.slot_id not in drop]


def _claimed_rule_ids(fulfillment):
    return {rule.id for rule in fulfillment.rules.all()} | {
        rule.id for rule in fulfillment.overrides.all()
    }


def _unmet_coverage(slots, fulfillments, ghosts):
    """
    Coverage labels still open after courses already in the degree are checked.

    Taken courses and suggested courses are the pool. A course carries at most
    two labels. Anything it matches is not scheduled as another course.
    """
    if not slots:
        return []
    codes = []
    for fulfillment in fulfillments:
        if fulfillment.full_code not in codes:
            codes.append(fulfillment.full_code)
    for ghost in ghosts:
        code = ghost.get("full_code")
        if code and code not in codes:
            codes.append(code)
    belongs = prewarm_belongs_cache({slot.rule for slot in slots}, codes) if codes else {}
    used = {}
    unmet = []
    for slot in slots:
        carrier = None
        for code in codes:
            if used.get(code, 0) >= MAX_COVERAGE_PER_COURSE:
                continue
            if belongs.get((slot.rule_id, code)):
                carrier = code
                break
        if carrier is None:
            unmet.append(slot)
            continue
        used[carrier] = used.get(carrier, 0) + 1
    return unmet


def _coverage_placeholder(slot, cu):
    return {
        "slot_ids": [slot.slot_id],
        "kind": "placeholder",
        "full_code": None,
        "fulfillment_id": None,
        "label": slot.label,
        "short_label": slot.label,
        "cu": float(cu),
        "rules": [slot.rule_id],
        "rule_q": slot.rule.q,
        "alternatives": [],
        "course_number": 10**9,
    }


def _pad_to_degree_credits(plan_rules, fulfillments, credits_cache, ghosts, coverage_slots=()):
    """
    Fill each degree up to Degree.credits.

    Open sector and foundational-approach labels take the first credits of that
    gap, and only within the gap. The rest are Free Elective stubs. A label a
    pool course already carries is not passed in. Components that split one
    degree share one floor. A course claimed by two degrees counts toward both.
    A course on the plan that fills no rule is elective credit for the first
    degree that still has a gap.

    Returns the new cards and the coverage slot ids a degree total accounted for,
    including labels that did not fit and so are not scheduled.
    """
    from degree.models import Degree

    groups = {}
    for component in plan_rules.composition.components:
        if component.relation not in _DEGREE_RELATIONS or component.owner_id is None:
            continue
        groups.setdefault(component.owner_id, []).append(component)
    if not groups:
        return [], set()

    degrees = {degree.id: degree for degree in Degree.objects.filter(id__in=groups)}

    ruleless = []
    for fulfillment in sorted(fulfillments, key=lambda row: row.full_code):
        if not _claimed_rule_ids(fulfillment):
            ruleless.append(credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS))

    rows = []
    for degree_id, components in groups.items():
        degree = degrees.get(degree_id)
        if degree is None or degree.credits is None:
            continue
        rule_ids = {rule.id for component in components for rule in component.rules}
        counted = Decimal(0)
        for fulfillment in fulfillments:
            if _claimed_rule_ids(fulfillment) & rule_ids:
                counted += credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)
        for ghost in ghosts:
            if set(ghost.get("rules") or []) & rule_ids:
                counted += Decimal(str(ghost["cu"]))
        anchor = sorted(
            components,
            key=lambda component: (
                component.relation != "degrees",
                not component.counts_toward_degree_cap,
                component.key,
            ),
        )[0]
        rows.append(
            {
                "key": anchor.key,
                "degree_id": degree_id,
                "required": Decimal(degree.credits),
                "counted": counted,
                "rule_ids": rule_ids,
            }
        )

    rows.sort(key=lambda row: row["degree_id"])
    for cu in ruleless:
        for row in rows:
            if row["required"] - row["counted"] > 0:
                row["counted"] += cu
                break

    padding = []
    consumed = set()
    for row in rows:
        owned = [slot for slot in coverage_slots if slot.rule_id in row["rule_ids"]]
        consumed.update(slot.slot_id for slot in owned)
        shortfall = row["required"] - row["counted"]
        if shortfall <= 0:
            continue
        pending = list(owned)
        for index, cu in enumerate(slot_cus(None, shortfall)):
            if pending:
                padding.append(_coverage_placeholder(pending.pop(0), cu))
                continue
            padding.append(
                {
                    "slot_ids": [f"slot:free:{row['key']}:{index}"],
                    "kind": "placeholder",
                    "full_code": None,
                    "fulfillment_id": None,
                    "label": FREE_ELECTIVE_LABEL,
                    "short_label": FREE_ELECTIVE_LABEL,
                    "cu": float(cu),
                    "rules": [],
                    "rule_q": None,
                    "alternatives": [],
                    "course_number": 10**9,
                }
            )
    return padding, consumed


def suggest(degree_plan):
    """
    Suggestions for one plan.

    Returns placements-without-semesters plus pin rows the packer must account for.
    One ghost may list several slot ids when `allocate_rules` shares the course.
    """
    slots = open_slots(degree_plan)

    fulfillments = list(degree_plan.fulfillments.prefetch_related("rules", "overrides"))
    plan_codes = [f.full_code for f in fulfillments]
    credits_cache = prewarm_credits_cache(plan_codes)
    plan_rules = map_rules_and_degrees(degree_plan)
    slots = cover_slots_with_planned_courses(slots, fulfillments, plan_rules, degree_plan)
    # Sectors and foundational approaches are labels on courses in the degree.
    # They are scheduled only as part of the credit gap, after real courses.
    open_rule_count = len(slots)
    coverage = [slot for slot in slots if is_coverage_rule(slot.rule)]
    slots = [slot for slot in slots if not is_coverage_rule(slot.rule)]
    # Specific courses and writing first. Business breadth and free electives last,
    # and those named stubs are never guessed into a single course.
    # A named single course goes first, so it can cover another open slot it is
    # allowed to share. Lists and restrictions are scheduled after that, as stubs.
    slots = sorted(slots, key=lambda slot: (sole_listed_code(slot.rule) is None, _fill_key(slot)))
    by_rule = {}
    for slot in slots:
        by_rule.setdefault(slot.rule_id, []).append(slot)
    sharing = sharing_from_fulfillments(fulfillments, plan_rules.rule_to_component, credits_cache)
    # A rule with no remaining slots is already satisfied, so later courses leave it alone.
    open_rule_ids = {slot.rule_id for slot in slots}
    satisfied = {rule for rule in plan_rules.rule_to_component if rule.id not in open_rule_ids}

    blocked_codes = set(plan_codes)
    blocked_listings = set(
        Course.objects.filter(full_code__in=plan_codes).values_list("primary_listing_id", flat=True)
    )
    blocked_listings.discard(None)

    # One candidate query per distinct open leaf, then one belongs-cache warm-up.
    rule_by_id = {}
    candidate_pool = {}
    for slot in slots:
        if slot.rule_id in candidate_pool:
            continue
        rule_by_id[slot.rule_id] = slot.rule
        # A list of courses, and every department or attribute rule, stays a stub.
        # Only a leaf that names one course is scheduled as that course.
        if schedule_exception(slot.rule) or not sole_listed_code(slot.rule):
            candidate_pool[slot.rule_id] = None
            continue
        candidate_pool[slot.rule_id] = _candidates(slot.rule, blocked_codes, blocked_listings)

    candidate_codes = [
        course.full_code
        for courses in candidate_pool.values()
        if courses
        for course in courses
    ]
    belongs_cache = prewarm_belongs_cache(
        set(plan_rules.rule_to_component),
        list(set(plan_codes) | set(candidate_codes)),
    )
    extra_codes = [code for code in candidate_codes if code not in credits_cache]
    credits_cache.update(prewarm_credits_cache(extra_codes))

    consumed = set()
    ghosts = []

    for slot in slots:
        if slot.slot_id in consumed:
            continue
        courses = candidate_pool.get(slot.rule_id)
        chosen = None
        selected_rules = set()
        if courses:
            for course in courses:
                if course.full_code in blocked_codes:
                    continue
                # A rejected candidate must not spend sharing allowance.
                snapshot = _snapshot_sharing(sharing)
                selected, _, _ = allocate_rules(
                    course.full_code,
                    plan_rules.rules_per_component,
                    plan_rules.rule_to_component,
                    plan_rules.double_counts,
                    rule_selected=slot.rule,
                    degree_plan=degree_plan,
                    satisfied_rules=set(satisfied),
                    belongs_cache=belongs_cache,
                    graduate_sharing=sharing,
                    credits_cache=credits_cache,
                    policy=plan_rules.composition.policy,
                )
                if slot.rule in selected:
                    chosen = course
                    selected_rules = selected
                    break
                _restore_sharing(sharing, snapshot)
        if chosen is None:
            listed = [
                code
                for code in (listed_course_codes(slot.rule) or [])
                if code not in blocked_codes
            ]
            ghosts.append(
                {
                    "slot_ids": [slot.slot_id],
                    "kind": "placeholder",
                    "full_code": None,
                    "fulfillment_id": None,
                    "label": slot.label,
                    "short_label": schedule_code(slot.rule),
                    "cu": float(slot.cu),
                    "rules": [slot.rule_id],
                    "rule_q": slot.rule.q,
                    "alternatives": listed,
                    "course_number": 10**9,
                }
            )
            consumed.add(slot.slot_id)
            continue

        covered = [slot.slot_id]
        covered_rules = [slot.rule_id]
        consumed.add(slot.slot_id)
        for rule in selected_rules:
            if rule.id == slot.rule_id:
                continue
            pending = [s for s in by_rule.get(rule.id, []) if s.slot_id not in consumed]
            if not pending:
                continue
            covered.append(pending[0].slot_id)
            covered_rules.append(rule.id)
            consumed.add(pending[0].slot_id)
            if not [s for s in by_rule.get(rule.id, []) if s.slot_id not in consumed]:
                satisfied.add(rule)

        if not [s for s in by_rule.get(slot.rule_id, []) if s.slot_id not in consumed]:
            satisfied.add(slot.rule)

        number = 10**9
        digits = "".join(ch for ch in chosen.full_code.split("-")[-1] if ch.isdigit())
        if digits:
            number = int(digits)
        alternatives = [
            other.full_code
            for other in courses
            if other.full_code != chosen.full_code and other.full_code not in blocked_codes
        ][:ALTERNATIVE_LIMIT]
        ghosts.append(
            {
                "slot_ids": covered,
                "kind": "course",
                "full_code": chosen.full_code,
                "fulfillment_id": None,
                "label": slot.label,
                "short_label": schedule_code(slot.rule),
                "cu": float(_credits(chosen, credits_cache)),
                "rules": covered_rules,
                "rule_q": slot.rule.q,
                "alternatives": alternatives,
                "course_number": number,
            }
        )
        _block(chosen, blocked_codes, blocked_listings)

    placements = []
    for fulfillment in unplaced_fulfillments(degree_plan):
        cu = credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)
        digits = "".join(ch for ch in fulfillment.full_code.split("-")[-1] if ch.isdigit())
        placements.append(
            {
                "slot_ids": [],
                "kind": "placement",
                "full_code": fulfillment.full_code,
                "fulfillment_id": fulfillment.id,
                "label": fulfillment.full_code,
                "cu": float(cu),
                "rules": [rule.id for rule in fulfillment.rules.all()],
                "rule_q": None,
                "alternatives": [],
                "course_number": int(digits) if digits else 10**9,
            }
        )

    pins = []
    for fulfillment in fulfillments:
        if not fulfillment.semester:
            continue
        pins.append(
            {
                "semester": fulfillment.semester,
                "cu": float(credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)),
                "full_code": fulfillment.full_code,
            }
        )

    ghosts = pair_placeholders(ghosts, plan_rules, sharing)
    unmet = _unmet_coverage(coverage, fulfillments, ghosts)
    padding, consumed = _pad_to_degree_credits(
        plan_rules, fulfillments, credits_cache, ghosts, coverage_slots=unmet
    )
    for slot in unmet:
        if slot.slot_id in consumed:
            continue
        ghosts.append(_coverage_placeholder(slot, slot.cu))
    ghosts.extend(padding)

    return {
        "items": placements + ghosts,
        "pins": pins,
        "open_rule_count": open_rule_count,
    }
