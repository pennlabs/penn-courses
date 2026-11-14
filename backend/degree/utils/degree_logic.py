import re
from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Exists, Q

from courses.models import Course
from degree.utils.double_counts import resolve_double_counts


# A submatriculant may double count at most this many CUs between their undergraduate and
# their graduate degree, and only graduate-level coursework is eligible. Path@Penn cannot
# express this: each audit's ShareWith policy is written about the blocks of that one audit,
# so two separately scraped audits both saying they share with (MAJOR) would otherwise share
# without limit. See the SEAS handbook, "Accelerated Master's (4+1) in Engineering".
MAX_SHARED_GRADUATE_CREDITS = Decimal(3)

# Coursework below this number never counts toward a graduate degree. A 4000-level course
# scheduled with a 5000+ one is also eligible, but nothing in the audit records which courses
# those were, so they are not treated as eligible here.
MIN_GRADUATE_COURSE_NUMBER = 5000

DEFAULT_COURSE_CREDITS = Decimal(1)

# Which of a submatriculant's degrees a course is on the books for. A transcript lists a course
# under its undergraduate record, its graduate record, or both; only a course on both records
# is double counted, and the rest may only count toward the degree whose record names them.
UNDERGRADUATE_LEVEL = "UNDERGRADUATE"
GRADUATE_LEVEL = "GRADUATE"
SHARED_LEVEL = "SHARED"
FULFILLMENT_LEVELS = [
    (UNDERGRADUATE_LEVEL, "Undergraduate only"),
    (GRADUATE_LEVEL, "Graduate only"),
    (SHARED_LEVEL, "Shared between both"),
]


def aggregate_rule_leaves(rules, f):
    """
    Given a list of rules and a function f,
    performs f on each leaf rule.
    """
    bfs_queue = deque()
    bfs_queue.extend(rules)
    while bfs_queue:
        for child in bfs_queue.pop().children.all():
            if child.q:
                f(child)
            else:
                bfs_queue.append(child)


def rule_subtrees(rules) -> set:
    """The given rules and every rule beneath them, fetched a level at a time."""
    from degree.models import Rule

    found = set()
    frontier = set(rules)
    while frontier:
        found |= frontier
        frontier = set(Rule.objects.filter(parent__in=frontier)) - found
    return found


class PickGroups:
    """
    The groups above some leaf rules that ask for only some of their children, like "one of
    these tracks". Once such a group has enough satisfied children, its other leaves need no
    more courses.
    """

    def __init__(self, leaves):
        from degree.models import Rule

        nodes = {rule.id: rule for rule in leaves}
        frontier = {rule.parent_id for rule in leaves if rule.parent_id} - set(nodes)
        while frontier:
            fetched = list(Rule.objects.filter(id__in=frontier))
            nodes.update((rule.id, rule) for rule in fetched)
            frontier = {rule.parent_id for rule in fetched if rule.parent_id} - set(nodes)

        self.children = defaultdict(list)
        for rule in nodes.values():
            if rule.parent_id in nodes:
                self.children[rule.parent_id].append(rule)
        self.groups = [
            rule
            for rule in nodes.values()
            if not rule.q and rule.num is not None and len(self.children[rule.id]) > rule.num
        ]

    def _leaves(self, rule):
        if rule.q:
            return [rule]
        return [leaf for child in self.children[rule.id] for leaf in self._leaves(child)]

    def closed(self, satisfied):
        """The leaves left unsatisfied under a group that is satisfied without them."""
        memo = {}

        def is_satisfied(rule):
            if rule.id not in memo:
                if rule.q:
                    memo[rule.id] = rule in satisfied
                else:
                    children = self.children[rule.id]
                    done = sum(is_satisfied(child) for child in children)
                    needed = len(children) if rule.num is None else rule.num
                    memo[rule.id] = bool(children) and done >= needed
            return memo[rule.id]

        return {
            leaf
            for group in self.groups
            if is_satisfied(group)
            for leaf in self._leaves(group)
            if leaf not in satisfied
        }


def check_dept(q, dept):
    pattern = r"\('([^']*)',\s*'([^']*)'\)"
    matches = re.findall(pattern, q)
    return any([match for match in matches if dept in match[1] and match[0] != "full_code"])


_LOOKUPS = {
    "exact": lambda value, arg: value == arg,
    "in": lambda value, arg: value in arg,
    "startswith": lambda value, arg: value.startswith(arg),
    "gt": lambda value, arg: value > arg,
    "gte": lambda value, arg: value >= arg,
    "lt": lambda value, arg: value < arg,
    "lte": lambda value, arg: value <= arg,
}


def matches_without_record(q, full_code):
    """
    Whether a course with no Course record, such as an AP credit code that is never scheduled,
    satisfies `q`. Its code is all that is known of it, so it has no attributes, semesters or
    anything else a q can ask about.
    """
    department, _, code = full_code.partition("-")
    fields = {"full_code": full_code, "department__code": department, "code": code}

    def leaf(lookup, arg):
        for field, value in fields.items():
            if lookup == field:
                return value == arg
            operator = lookup.removeprefix(f"{field}__")
            if operator != lookup and operator in _LOOKUPS:
                return _LOOKUPS[operator](value, arg)
        return False

    def node(q):
        results = (node(child) if isinstance(child, Q) else leaf(*child) for child in q.children)
        matched = all(results) if q.connector == Q.AND else any(results)
        return matched != q.negated

    return node(q)


def recorded_full_codes(full_codes):
    return set(Course.objects.filter(full_code__in=full_codes).values_list("full_code", flat=True))


def check_belongs(rule, full_code, belongs_cache, is_transfer=False):
    """
    Rule.check_belongs, memoized in the given dict. Each rule is asked about the same course
    several times while allocating it (once to prioritize, once per double count, once to
    collect the leftovers), and every uncached call is a database query.
    """
    if not rule.accepts(is_transfer=is_transfer):
        return False
    key = (rule.id, full_code)
    if key not in belongs_cache:
        belongs_cache[key] = rule.check_belongs(full_code)
    return belongs_cache[key]


def prewarm_belongs_cache(rules, full_codes):
    """
    Returns a belongs_cache (see check_belongs) filled in for every combination of the given
    leaf rules and courses, using one query per rule rather than one per rule/course pair.
    Worth doing when every course is known up front, e.g. when allocating a whole transcript.
    """
    belongs_cache = {}
    unrecorded = set(full_codes) - recorded_full_codes(full_codes)

    for rule in rules:
        if not rule.q:
            continue
        q = rule.get_q_object() or Q()
        matched = set(
            Course.objects.filter(q, full_code__in=full_codes).values_list("full_code", flat=True)
        )
        matched |= {full_code for full_code in unrecorded if matches_without_record(q, full_code)}
        for full_code in full_codes:
            belongs_cache[(rule.id, full_code)] = full_code in matched

    return belongs_cache


def prewarm_belongs_cache_for_course(rules, full_code):
    """A belongs_cache for one course, filled by a single query instead of one per rule."""
    rules = [rule for rule in rules if rule.q]
    if not rules:
        return {}

    columns = {f"rule_{rule.id}": rule for rule in rules}
    matched = (
        Course.objects.filter(full_code=full_code)
        .annotate(
            **{
                column: Exists(Course.objects.filter(rule.get_q_object(), full_code=full_code))
                for column, rule in columns.items()
            }
        )
        .values(*columns)
        .first()
    )
    if matched is None:
        return {
            (rule.id, full_code): matches_without_record(rule.get_q_object(), full_code)
            for rule in rules
        }

    return {(rule.id, full_code): matched.get(column, False) for column, rule in columns.items()}


def prewarm_credits_cache(full_codes):
    """
    Returns the CU of each of the given courses, for weighing against the sharing allowance.
    A course PDP does not know is assumed to be worth DEFAULT_COURSE_CREDITS.
    """
    return {
        full_code: credits
        for full_code, credits in Course.objects.filter(full_code__in=full_codes)
        .exclude(credits__isnull=True)
        .values_list("full_code", "credits")
    }


def is_graduate(component) -> bool:
    """
    Whether a plan component awards a graduate degree. Only degrees carry a program code, so
    majors and minors are never graduate. A composed Component carries the flag directly.
    """
    if component is None:
        return False
    flag = getattr(component, "is_graduate", None)
    if isinstance(flag, bool):
        return flag
    # Imported here because degree.models imports this module; sys.modules makes the repeat
    # lookup cheap.
    from degree.models import graduate_programs

    return getattr(component, "program", None) in graduate_programs


def level_allows(level, component) -> bool:
    """
    Whether a course of the given level may count toward a plan component. A level of None
    (a course not read off a transcript) and SHARED allow every component.
    """
    if level == GRADUATE_LEVEL:
        return is_graduate(component)
    if level == UNDERGRADUATE_LEVEL:
        return not is_graduate(component)
    return True


def course_number(full_code: str):
    """The numeric part of a course code, e.g. 5200 for CIS-5200. None if there is not one."""
    match = re.search(r"-(\d+)", full_code or "")
    return int(match.group(1)) if match else None


def is_graduate_coursework(full_code: str) -> bool:
    number = course_number(full_code)
    return number is not None and number >= MIN_GRADUATE_COURSE_NUMBER


def level_for_course(full_code: str, level):
    """A course numbered below graduate coursework can only be on the undergraduate record."""
    if level in (GRADUATE_LEVEL, SHARED_LEVEL) and not is_graduate_coursework(full_code):
        return UNDERGRADUATE_LEVEL
    return level


class GraduateSharing:
    """
    Tracks how much of a plan's sharing allowances have been used.

    One instance spans all of a plan's courses, and courses are allocated in the order they
    were taken, so an allowance goes to the earliest eligible courses. That is a default
    rather than an optimum: the student can still move a course by hand afterwards.

    `used` / `allows` / `take` are the undergraduate-graduate allowance. `program_shared_cu_used`
    is a coordinated program's own cap. `claims` records which components already hold a course,
    keyed by the course's canonical (cross-list) code.
    """

    def __init__(self, limit=MAX_SHARED_GRADUATE_CREDITS):
        self.limit = limit
        self.used = Decimal(0)
        self.program_shared_cu_used = Decimal(0)
        self.claims = defaultdict(set)

    def allows(self, credits) -> bool:
        return self.used + credits <= self.limit

    def take(self, credits) -> None:
        self.used += credits


# The composition pass and the submatriculation cap share one tracker.
SharingState = GraduateSharing


def split_by_level(selected_rules, rule_to_degree):
    """
    Partitions selected rules into those belonging to a graduate degree and those belonging to
    any other component. Rules of no component in the plan (e.g. an override) are left out.
    """
    graduate, undergraduate = set(), set()
    for rule in selected_rules:
        component = rule_to_degree.get(rule)
        if component is None:
            continue
        (graduate if is_graduate(component) else undergraduate).add(rule)
    return graduate, undergraduate


def apply_graduate_sharing(
    full_code, selected_rules, unselected_rules, rule_to_degree, sharing, credits
):
    """
    Applies the submatriculation double counting allowance to one course's selections.

    A course shared between a graduate degree and an undergraduate one spends the allowance. If
    it is not graduate-level coursework, or the allowance is spent, the course keeps only its
    undergraduate rules and its graduate ones are offered as unselected instead, so nothing is
    silently dropped and the student can still choose it by hand.
    """
    graduate_rules, undergraduate_rules = split_by_level(selected_rules, rule_to_degree)
    if not graduate_rules or not undergraduate_rules:
        # Counts toward only one level, so no allowance is spent.
        return selected_rules, unselected_rules

    if is_graduate_coursework(full_code) and sharing.allows(credits):
        sharing.take(credits)
        return selected_rules, unselected_rules

    return selected_rules - graduate_rules, unselected_rules | graduate_rules


def prewarm_canonical_cache(full_codes):
    """
    Maps each course code to the full code of its primary cross-listing. Two codes for one
    course then count as one claim.
    """
    cache = {}
    courses = Course.objects.filter(full_code__in=full_codes).select_related("primary_listing")
    for course in courses:
        primary = course.primary_listing
        cache[course.full_code] = primary.full_code if primary is not None else course.full_code
    for full_code in full_codes:
        cache.setdefault(full_code, full_code)
    return cache


def _component_score(rules, full_code):
    """Prefer a rule that names the course, then the one that asks for the most credit."""
    named = any(full_code and full_code in (rule.q or "") for rule in rules)
    weight = max((Decimal(rule.credits or rule.num or 0) for rule in rules), default=Decimal(0))
    return (1 if named else 0, weight)


def _cap_components(selected_rules, rule_to_component):
    grouped = {}
    for rule in selected_rules:
        component = rule_to_component.get(rule)
        if component is None or not component.counts_toward_degree_cap:
            continue
        grouped.setdefault(component.key, (component, []))
        grouped[component.key][1].append(rule)
    return grouped


def _demote(selected_rules, unselected_rules, rules):
    for rule in rules:
        selected_rules.discard(rule)
        unselected_rules.add(rule)


def apply_sharing_policy(
    full_code,
    selected_rules,
    unselected_rules,
    rule_to_component,
    policy,
    sharing,
    credits,
    canonical=None,
):
    """
    Plan-level sharing the audits cannot express, applied after each component has had its say.

    Order matches the degree planner's conflict repair: at most two degree claims for a course,
    then a coordinated program's shared-CU cap, then the undergraduate/graduate cap, then
    graduate programs not sharing a graduate course with each other.
    """
    selected_rules = set(selected_rules)
    unselected_rules = set(unselected_rules)
    canonical = canonical or full_code
    already = set(sharing.claims.get(canonical, ()))

    grouped = _cap_components(selected_rules, rule_to_component)
    newcomers = [key for key in grouped if key not in already]
    room = policy.max_degree_claims - len(already)
    if room < len(newcomers):
        ranked = sorted(
            newcomers,
            key=lambda key: _component_score(grouped[key][1], full_code),
            reverse=True,
        )
        keep = max(room, 0)
        for key in ranked[keep:]:
            _demote(selected_rules, unselected_rules, grouped[key][1])

    if policy.max_shared_cu is not None:
        sides = set()
        side_rules = {"left": [], "right": []}
        for rule in selected_rules:
            component = rule_to_component.get(rule)
            if component is not None and component.side in side_rules:
                sides.add(component.side)
                side_rules[component.side].append(rule)
        if sides == {"left", "right"}:
            if sharing.program_shared_cu_used + credits <= policy.max_shared_cu:
                sharing.program_shared_cu_used += credits
            else:
                weaker = min(
                    ("left", "right"),
                    key=lambda side: _component_score(side_rules[side], full_code),
                )
                _demote(selected_rules, unselected_rules, side_rules[weaker])

    selected_rules, unselected_rules = apply_graduate_sharing(
        full_code,
        selected_rules,
        unselected_rules,
        rule_to_component,
        sharing,
        credits,
    )

    if policy.forbid_grad_grad:
        graduate = {}
        for rule in selected_rules:
            component = rule_to_component.get(rule)
            if component is not None and component.is_graduate:
                graduate.setdefault(component.key, []).append(rule)
        if len(graduate) > 1:
            ranked = sorted(
                graduate,
                key=lambda key: _component_score(graduate[key], full_code),
                reverse=True,
            )
            for key in ranked[1:]:
                _demote(selected_rules, unselected_rules, graduate[key])

    sharing.claims.setdefault(canonical, set()).update(
        _cap_components(selected_rules, rule_to_component)
    )
    return selected_rules, unselected_rules


def selection_is_legal(selected_rules, rule_to_component, double_counts, policy=None):
    """ShareWith legality, plus the plan-level cap on how many degrees may claim a course."""
    if not check_legal(selected_rules, rule_to_component, double_counts):
        return False
    if policy is None or not policy.cross_component_sharing:
        return True
    claimed = {
        rule_to_component[rule].key
        for rule in selected_rules
        if rule_to_component.get(rule) is not None
        and rule_to_component[rule].counts_toward_degree_cap
    }
    return len(claimed) <= policy.max_degree_claims


def sharing_from_fulfillments(fulfillments, rule_to_degree, credits_cache=None):
    """
    A GraduateSharing already charged for what a plan's stored fulfillments share between its
    graduate and undergraduate degrees, for weighing one more course against what is left.
    """
    sharing = GraduateSharing()
    for fulfillment in fulfillments:
        graduate, undergraduate = split_by_level(fulfillment.rules.all(), rule_to_degree)
        if graduate and undergraduate:
            sharing.take((credits_cache or {}).get(fulfillment.full_code, DEFAULT_COURSE_CREDITS))
    return sharing


def can_share(rule, others, double_counts):
    """
    Whether `rule` is allowed to double count with every rule in `others`. A rule always
    shares with itself.
    """
    allowed = double_counts.get(rule, set())
    return all(other == rule or other in allowed for other in others)


def reconcile_rules(rules, preferred, rule_to_degree, double_counts):
    """
    Thins a set of rules selected for one course down to rules that may all share it.

    `preferred` rules are kept first (they are what the student just asked for), then every
    other rule that may share with everything kept so far, in id order so the result is
    deterministic. Rules that are not leaf rules of the plan, such as a stale override, are
    kept as they are, which is also how check_legal treats them.

    Returns the rules kept and the rules demoted.
    """
    kept = set()

    def fits(rule):
        if rule_to_degree.get(rule) is None:
            return True
        return can_share(
            rule, {r for r in kept if rule_to_degree.get(r) is not None}, double_counts
        )

    preferred = set(preferred)
    ordered = sorted(preferred, key=lambda r: r.id) + sorted(
        set(rules) - preferred, key=lambda r: r.id
    )
    for rule in ordered:
        if fits(rule):
            kept.add(rule)

    return kept, set(ordered) - kept


def scarcity(rule):
    """Sorts the rules with the fewest alternative courses first. An uncounted rule goes last."""
    return (rule.match_count is None, rule.match_count or 0)


def get_priority_rule(rules, full_code, belongs_cache, is_transfer=False):
    """
    The applicable rule a course should fill first: the one with the fewest alternative courses,
    so scarce requirements are filled before catch-alls. Ties, including every rule of a plan
    whose counts have not been refreshed yet, go to a rule naming the course, then to the rule
    needing the most, then to the lowest id.
    """

    def rank(rule):
        return (
            scarcity(rule),
            full_code not in rule.q,
            -(rule.credits or rule.num or 0),
            rule.id,
        )

    return min(
        (r for r in rules if check_belongs(r, full_code, belongs_cache, is_transfer=is_transfer)),
        key=rank,
        default=None,
    )


def allocate_rules(
    full_code,
    rules_per_degree,
    rule_to_degree,
    double_counts,
    rule_selected=None,
    degree_plan=None,
    satisfied_rules=None,
    belongs_cache=None,
    is_transfer=False,
    graduate_sharing=None,
    credits_cache=None,
    policy=None,
    canonical=None,
    prior_selected=None,
    level=None,
):
    """
    Given a course (full_code), rule, degree and double count mappings, and optionally a selected
    rule, degree plan, list of satisfied rules, and a belongs_cache (see prewarm_belongs_cache),
    returns rules (of all degrees in degreeplans) to show as selected by the course, rules to
    show as unselected, and if the selections are legal.

    `is_transfer` says the course is AP or transfer credit, which keeps it off every rule that
    does not accept such credit.

    `level` is which of a submatriculant's records the course is on (see FULFILLMENT_LEVELS).
    A course on only one record counts toward only that level's components; the other level's
    rules are not offered at all, because the registrar does not let the course count there.

    `prior_selected` is what the course already counts for, when it is already in the plan.
    Those choices are kept, except where they conflict with `rule_selected`, and the
    allocation only adds what may share with them.
    """
    if rule_selected is not None and not rule_selected.accepts(is_transfer=is_transfer):
        rule_selected = None
    selected_rules = set()
    unselected_rules = set()
    if belongs_cache is None:
        belongs_cache = prewarm_belongs_cache_for_course(rule_to_degree, full_code)
    rules_per_degree = {
        degree: rules for degree, rules in rules_per_degree.items() if level_allows(level, degree)
    }
    if prior_selected:

        def allowed(rule):
            return (
                rule in rule_to_degree
                and level_allows(level, rule_to_degree[rule])
                and rule.accepts(is_transfer=is_transfer)
            )

        seed = {rule for rule in prior_selected if allowed(rule)}
        preferred = {rule_selected} if allowed(rule_selected) else set()
        selected_rules, _ = reconcile_rules(
            seed | preferred, preferred, rule_to_degree, double_counts
        )
    if satisfied_rules is None:
        satisfied_rules = degree_plan.check_rules_already_satisfied(
            {rule for rules in rules_per_degree.values() for rule in rules}
        )

    # Each component chooses in turn, and may only choose what every earlier component's
    # choice is allowed to share with, so the union is legal by construction. The component
    # the course was dropped onto goes first: its choice is the one the student made.
    components = sorted(
        rules_per_degree, key=lambda degree: rule_selected not in rules_per_degree[degree]
    )
    for degree in components:
        rules = rules_per_degree[degree].copy()

        # Find rule whose double counts we should consider. If we're in the right degree,
        # then it's rule_selected.
        chosen_rule = (
            rule_selected
            if rule_selected in rules
            else get_priority_rule(
                {
                    rule
                    for rule in rules.difference(satisfied_rules)
                    if can_share(rule, selected_rules, double_counts)
                },
                full_code,
                belongs_cache,
                is_transfer=is_transfer,
            )
        )
        addl_selected_rules, addl_unselected_rules = assign_individual_rule(
            full_code,
            chosen_rule,
            rules,
            satisfied_rules,
            rule_to_degree,
            double_counts,
            belongs_cache,
            is_transfer=is_transfer,
            prior_selected=selected_rules,
        )

        selected_rules |= {
            rule for rule in addl_selected_rules if rule_to_degree.get(rule) == degree
        }
        unselected_rules |= {
            rule for rule in addl_unselected_rules if rule_to_degree.get(rule) == degree
        }

    # A seeded rule is still walked by its component's pass, which offers it as unselected.
    unselected_rules -= selected_rules

    # Plan-level caps the audits cannot state. With a policy, that includes the two-claim
    # limit and a coordinated program's shared-CU cap as well as the submatriculation cap.
    # Without one, only the submatriculation cap runs, which is what older callers pass.
    course_credits = (credits_cache or {}).get(full_code, DEFAULT_COURSE_CREDITS)
    if policy is not None and graduate_sharing is not None:
        selected_rules, unselected_rules = apply_sharing_policy(
            full_code,
            selected_rules,
            unselected_rules,
            rule_to_degree,
            policy,
            graduate_sharing,
            course_credits,
            canonical=canonical or full_code,
        )
    elif graduate_sharing is not None:
        selected_rules, unselected_rules = apply_graduate_sharing(
            full_code,
            selected_rules,
            unselected_rules,
            rule_to_degree,
            graduate_sharing,
            course_credits,
        )

    # ShareWith is legal by construction; the policy caps are checked too.
    legal = selection_is_legal(selected_rules, rule_to_degree, double_counts, policy)

    return selected_rules, unselected_rules, legal


@dataclass(eq=False)
class CourseAllocation:

    full_code: str
    selected: set
    unselected: set


def within_policy(before, after, rule_to_component, policy):
    """
    Whether changing a course's rules from `before` to `after` keeps to the plan-level caps that
    `apply_sharing_policy` enforces. A coordinated program's shared-CU cap was spent in the order
    courses were taken, so a course may not newly count toward both of its sides.
    """
    if policy is None:
        return True
    if len(_cap_components(after, rule_to_component)) > policy.max_degree_claims:
        return False
    if policy.forbid_grad_grad:
        graduate = {
            rule_to_component[rule].key
            for rule in after
            if rule in rule_to_component and is_graduate(rule_to_component[rule])
        }
        if len(graduate) > 1:
            return False
    if policy.max_shared_cu is not None:

        def sides(rules):
            return {
                rule_to_component[rule].side
                for rule in rules
                if rule in rule_to_component
                and getattr(rule_to_component[rule], "side", None) in ("left", "right")
            }

        if sides(after) == {"left", "right"} and sides(before) != {"left", "right"}:
            return False
    return True


def rebalance_allocations(
    allocations,
    rule_to_degree,
    double_counts,
    credits_cache=None,
    allows=None,
    exempt=frozenset(),
):
    """
    Moves courses onto short rules when another course can take their place, without leaving any
    rule worse off or breaking double counting limits.

    Only for allocating a whole plan, since it can move any course. `allocations` must be in the
    order the courses were taken, and is changed in place. `allows(before, after)` vetoes a
    change to one course's rules, e.g. one the plan's sharing caps forbid. Rules in `exempt`,
    such as waived ones, need no courses and are never short.
    """
    credits_cache = credits_cache or {}

    def credits_of(allocation):
        return credits_cache.get(allocation.full_code, DEFAULT_COURSE_CREDITS)

    def is_short(rule, courses):
        if rule in exempt:
            return False
        if rule.num and len(courses) < rule.num:
            return True
        return bool(rule.credits and sum(credits_of(c) for c in courses) < rule.credits)

    def starts_crossing_levels(allocation, rules):
        def crosses(selected):
            graduate, undergraduate = split_by_level(selected, rule_to_degree)
            return bool(graduate and undergraduate)

        return crosses(rules) and not crosses(allocation.selected)

    members = defaultdict(set)
    for allocation in allocations:
        for rule in allocation.selected:
            members[rule].add(allocation)

    def find_replacement(rule, leaving, taken):
        options = [
            other
            for other in allocations
            if other is not leaving
            and other not in taken
            and rule in other.unselected
            and credits_of(other) >= credits_of(leaving)
            and can_share(rule, other.selected, double_counts)
            and not starts_crossing_levels(other, other.selected | {rule})
            and (allows is None or allows(other.selected, other.selected | {rule}))
        ]
        return min(options, key=lambda other: bool(other.selected), default=None)

    def plan_move(allocation, rule):
        """The replacement each of this course's rules needs if it moves to `rule`, or None."""
        conflicts = {
            other
            for other in allocation.selected
            if other in rule_to_degree and not can_share(rule, {other}, double_counts)
        }
        moved = (allocation.selected - conflicts) | {rule}
        if starts_crossing_levels(allocation, moved):
            return None
        if allows is not None and not allows(allocation.selected, moved):
            return None

        replacements = {}
        for conflict in conflicts:
            if not is_short(conflict, members[conflict] - {allocation}):
                continue
            replacement = find_replacement(conflict, allocation, set(replacements.values()))
            if replacement is None:
                return None
            replacements[conflict] = replacement
        return conflicts, replacements

    for rule in sorted(rule_to_degree, key=lambda rule: (scarcity(rule), rule.id)):
        for allocation in allocations:
            if not is_short(rule, members[rule]):
                break
            if rule not in allocation.unselected:
                continue
            move = plan_move(allocation, rule)
            if move is None:
                continue

            conflicts, replacements = move
            allocation.selected -= conflicts
            allocation.unselected |= conflicts
            for conflict in conflicts:
                members[conflict].discard(allocation)
            allocation.selected.add(rule)
            allocation.unselected.discard(rule)
            members[rule].add(allocation)
            for conflict, replacement in replacements.items():
                replacement.selected.add(conflict)
                replacement.unselected.discard(conflict)
                members[conflict].add(replacement)


def assign_individual_rule(
    full_code,
    chosen_rule,
    rules,
    satisfied_rules,
    rule_to_degree,
    double_counts,
    belongs_cache,
    is_transfer=False,
    prior_selected=frozenset(),
):
    """
    Given a course (full_code), a chosen rule, other rules, already satisfied rules, and the
    double counts allowed between rules, returns new sets of optimized selected and unselected
    rules relating to this full_code.

    `prior_selected` holds what other components already selected for this course. Nothing
    is selected here that may not double count with all of it; such rules are offered as
    unselected instead, so the student can still choose them by hand.
    """
    # Add rules that can double count with chosen rule, and remove them from future
    # consideration.
    selected_rules = set()
    unselected_rules = set()

    if chosen_rule:
        # Only double count where mutually allowed
        # Ex. Adding CIS 5550 -> area lists double count with all other area lists,
        # cis electives, tech electives, etc. However, we can't add CIS 5550 to
        # both cis electives and tech electives, and they're not mutually double
        # countable

        relevant_dcrs = {
            r
            for r in double_counts.get(chosen_rule, set())
            if r not in satisfied_rules
            and check_belongs(r, full_code, belongs_cache, is_transfer=is_transfer)
            and can_share(r, prior_selected, double_counts)
        }
        relevant_dcrs.add(chosen_rule)

        # A rule is mutual if every other relevant rule double counts with it (a rule always
        # double counts with itself, hence the union)
        mutual_rules = {
            rule
            for rule in relevant_dcrs
            if relevant_dcrs <= double_counts.get(rule, set()) | {rule}
        }
        pick_one_rules = relevant_dcrs - mutual_rules

        selected_rules = selected_rules.union(mutual_rules)
        rules.difference_update(mutual_rules)

        # Pick one of the pick_one_rules (if not chosen rule, it's random right now)
        if len(pick_one_rules):
            picked_rule = (
                chosen_rule
                if chosen_rule in pick_one_rules
                else get_priority_rule(
                    pick_one_rules, full_code, belongs_cache, is_transfer=is_transfer
                )
            )
            if picked_rule:
                selected_rules.add(picked_rule)
                rules.discard(picked_rule)

    # Consider all other rules within degree. If satisfies, add to unselected rules.
    # However, if full_code is listed by name, the rule is currently unsatisfied, and nothing
    # already selected forbids sharing with it, select it too.
    existing_degrees = [rule_to_degree.get(r) for r in selected_rules]
    for rule in rules:
        if not check_belongs(rule, full_code, belongs_cache, is_transfer=is_transfer):
            continue
        if full_code in rule.q and rule not in satisfied_rules:
            # check if this rule's degree is different from all degrees in selected_rules
            rule_degree = rule_to_degree.get(rule)
            if rule_degree not in existing_degrees and can_share(
                rule, selected_rules | set(prior_selected), double_counts
            ):
                selected_rules.add(rule)
            else:
                unselected_rules.add(rule)
        else:
            unselected_rules.add(rule)

    return selected_rules, unselected_rules


def check_legal(selected_rules, rule_to_degree, double_counts):
    """
    Given a list of selected rules, rule to degree mappings, and the double counts allowed
    between rules, returns True if all selected rules can be double counted with each other
    and False otherwise.

    Sharing is policed across the whole plan, not just within a single degree: the audit's
    ShareWith policy is written in terms of block types, and targets like (MAJOR) and (MINOR)
    are statements about *other* programs, so restricting the check to one degree at a time
    would ignore most of what the policy says.
    """
    for rule in selected_rules:
        if rule_to_degree.get(rule) is None:
            # not a leaf rule of any degree in the plan (e.g. an override)
            continue
        allowed = double_counts.get(rule, set())
        if any(
            r not in allowed and r != rule and rule_to_degree.get(r) is not None
            for r in selected_rules
        ):
            return False
    return True


def plan_components(degree_plan):
    """
    Everything in a plan that contributes rules: its degrees, plus any additional majors and
    minors. Each is a separate unit for double counting, which is what lets a course satisfy
    a rule in the major and one in a minor while still being exclusive within either.
    """
    return [
        *degree_plan.degrees.all(),
        *degree_plan.majors.all(),
        *degree_plan.minors.all(),
    ]


def map_rules_and_degrees(degree_plan):
    """
    Given a degree plan, produces mappings of rules to the component they belong to, and of
    each rule to the rules it is allowed to double count with.

    The mapping key is a Component. Iterating the return value still yields
    `(rules_per_component, rule_to_component, double_counts)`.
    """
    from degree.utils.composition import PlanRules, compose

    composition = compose(degree_plan)
    rules_per_degree = {}
    rule_to_degree = {}
    trees = {}
    for component in composition.components:
        leaves = [rule for rule in component.rules if rule.q]
        rules_per_degree[component] = set(leaves)
        trees[component] = leaves
        for rule in leaves:
            rule_to_degree[rule] = component

    return PlanRules(
        rules_per_degree,
        rule_to_degree,
        resolve_double_counts(trees, undergraduate_degree_of(degree_plan, composition.components)),
        composition,
    )


# Components that stand for a degree's own audit: the degree itself, or, for a College double
# major, its general education and its major block.
DEGREE_RELATIONS = {"degrees", "college", "degree-major"}


def undergraduate_degree_of(degree_plan, components):
    """
    Maps each component to the undergraduate degree whose audit it belongs to: a degree to
    itself, and a major or minor to the degree the student placed it under, if that degree is in
    the plan.
    """
    from degree.models import DegreePlanMajor, DegreePlanMinor

    degree_ids = {
        c.owner_id for c in components if c.relation in DEGREE_RELATIONS and not c.is_graduate
    }
    placed = {
        relation: dict(
            placement.objects.filter(degree_plan=degree_plan, degree_id__in=degree_ids).values_list(
                field, "degree_id"
            )
        )
        for relation, placement, field in (
            ("majors", DegreePlanMajor, "major_id"),
            ("minors", DegreePlanMinor, "minor_id"),
        )
    }
    result = {}
    for component in components:
        if component.relation in DEGREE_RELATIONS:
            if component.owner_id in degree_ids:
                result[component] = component.owner_id
        elif component.owner_id in placed.get(component.relation, {}):
            result[component] = placed[component.relation][component.owner_id]
    return result


def cas_credit_summary(composition, fulfillments, credits_cache):
    """
    College double major: one credit floor, major CU reduced by courses that landed in more
    than one major, and whatever is left after the college requirements.
    """
    if composition.kind != "cas_double_major" or composition.college_owner_id is None:
        return None

    from degree.models import Degree

    def rule_required(rule, owned):
        """None when no leaf under `rule` belongs to the component."""
        if rule.q:
            if rule.id not in owned:
                return None
            if rule.credits is not None:
                return rule.credits
            return Decimal(rule.num) if rule.num is not None else Decimal(0)
        children = sorted(
            value
            for value in (rule_required(child, owned) for child in rule.children.all())
            if value is not None
        )
        if not children:
            return None
        if rule.credits is not None:
            return rule.credits
        if rule.num is not None:
            children = children[: rule.num]
        return sum(children, Decimal(0))

    def required(component):
        # College and major components share the degree's roots but own disjoint leaves.
        owned = {rule.id for rule in component.rules}
        values = (rule_required(root, owned) for root in component.roots)
        return sum((value for value in values if value is not None), Decimal(0))

    majors = [component for component in composition.components if component.role == "major"]
    college = next(
        (component for component in composition.components if component.role == "college"), None
    )
    by_code = defaultdict(set)
    for fulfillment in fulfillments:
        for rule in fulfillment.rules.all():
            for component in majors:
                if rule in component.rules:
                    by_code[fulfillment.full_code].add(component.key)
    shared = sum(
        (credits_cache.get(full_code) or DEFAULT_COURSE_CREDITS)
        for full_code, keys in by_code.items()
        if len(keys) >= 2
    )
    major_required = sum((required(component) for component in majors), Decimal(0))
    major_cu = max(major_required - shared, Decimal(0))
    college_cu = required(college) if college is not None else Decimal(0)
    degree = Degree.objects.filter(id=composition.college_owner_id).first()
    floor = degree.credits if degree is not None and degree.credits is not None else Decimal(36)
    return {
        "floor": floor,
        "major_cu": major_cu,
        "shared_cu": shared,
        "remaining": floor - college_cu - major_cu,
    }


def summarize_plan(degree_plan, fulfillments):
    """Claims, cap violations and the College remainder for a plan's stored fulfillments."""
    plan_rules = map_rules_and_degrees(degree_plan)
    composition = plan_rules.composition
    policy = composition.policy
    rule_to_component = plan_rules.rule_to_component
    credits_cache = prewarm_credits_cache([fulfillment.full_code for fulfillment in fulfillments])
    canonicals = prewarm_canonical_cache([fulfillment.full_code for fulfillment in fulfillments])

    claims = {}
    violations = []
    sharing = GraduateSharing(limit=policy.graduate_cu_limit)
    ordered = sorted(
        fulfillments, key=lambda fulfillment: (fulfillment.semester or "", fulfillment.full_code)
    )
    for fulfillment in ordered:
        selected = list(fulfillment.rules.all())
        grouped = _cap_components(selected, rule_to_component)
        claims[fulfillment.full_code] = sorted(grouped)
        if len(grouped) > policy.max_degree_claims:
            violations.append(
                {
                    "full_code": fulfillment.full_code,
                    "kind": "too_many_degrees",
                    "components": sorted(grouped),
                }
            )
        graduate, undergraduate = split_by_level(selected, rule_to_component)
        number = course_number(fulfillment.full_code)
        credits = credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)
        if graduate and undergraduate:
            eligible = number is not None and number >= policy.min_graduate_number
            if not eligible or not sharing.allows(credits):
                violations.append(
                    {
                        "full_code": fulfillment.full_code,
                        "kind": "undergrad_grad_cu",
                        "components": sorted(grouped),
                    }
                )
            else:
                sharing.take(credits)
        if (
            policy.forbid_grad_grad
            and len({rule_to_component[rule].key for rule in graduate if rule in rule_to_component})
            > 1
        ):
            violations.append(
                {
                    "full_code": fulfillment.full_code,
                    "kind": "grad_grad",
                    "components": sorted(grouped),
                }
            )
        canonical = canonicals.get(fulfillment.full_code, fulfillment.full_code)
        sharing.claims.setdefault(canonical, set()).update(grouped)

    return {
        "kind": composition.kind,
        "dual_program": (
            {"code": composition.dual_program.code, "name": composition.dual_program.name}
            if composition.dual_program is not None
            else None
        ),
        "course_claims": claims,
        "violations": violations,
        "cas": cas_credit_summary(composition, fulfillments, credits_cache),
    }
