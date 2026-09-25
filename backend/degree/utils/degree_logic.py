import re
from collections import defaultdict, deque
from decimal import Decimal

from django.db.models import Q

from courses.models import Course
from degree.utils.double_counts import get_degree_trees, resolve_double_counts


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


def check_dept(q, dept):
    pattern = r"\('([^']*)',\s*'([^']*)'\)"
    matches = re.findall(pattern, q)
    return any([match for match in matches if dept in match[1] and match[0] != "full_code"])


def check_belongs(rule, full_code, belongs_cache):
    """
    Rule.check_belongs, memoized in the given dict. Each rule is asked about the same course
    several times while allocating it (once to prioritize, once per double count, once to
    collect the leftovers), and every uncached call is a database query.
    """
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

    for rule in rules:
        if not rule.q:
            continue
        matched = set(
            Course.objects.filter(rule.get_q_object() or Q(), full_code__in=full_codes).values_list(
                "full_code", flat=True
            )
        )
        for full_code in full_codes:
            belongs_cache[(rule.id, full_code)] = full_code in matched

    return belongs_cache


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
    Whether a plan component (a Degree, Major or Minor) awards a graduate degree. Only degrees
    carry a program code, so majors and minors are never graduate.
    """
    # Imported here because degree.models imports this module; sys.modules makes the repeat
    # lookup cheap.
    from degree.models import graduate_programs

    return getattr(component, "program", None) in graduate_programs


def course_number(full_code: str):
    """The numeric part of a course code, e.g. 5200 for CIS-5200. None if there is not one."""
    match = re.search(r"-(\d+)", full_code or "")
    return int(match.group(1)) if match else None


class GraduateSharing:
    """
    Tracks how much of a submatriculant's double counting allowance a plan has used.

    One instance spans all of a plan's courses, and courses are allocated in the order they
    were taken, so the allowance goes to the earliest eligible courses. That is a default
    rather than an optimum: the student can still move a course by hand afterwards.
    """

    def __init__(self, limit=MAX_SHARED_GRADUATE_CREDITS):
        self.limit = limit
        self.used = Decimal(0)

    def allows(self, credits) -> bool:
        return self.used + credits <= self.limit

    def take(self, credits) -> None:
        self.used += credits


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

    number = course_number(full_code)
    if number is not None and number >= MIN_GRADUATE_COURSE_NUMBER and sharing.allows(credits):
        sharing.take(credits)
        return selected_rules, unselected_rules

    return selected_rules - graduate_rules, unselected_rules | graduate_rules


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


def get_priority_rule(rules, full_code, belongs_cache):
    """
    Primitive method for finding the rule of highest priority given a set of applicable rules.
    If the rule is explicitly mentioned, returns that rule. Else, returns the rule with the highest
    required CU count.
    """
    priority_rule = None
    priority_CUs = float("-inf")

    for r in rules:
        if full_code in r.q:
            return r

        if check_belongs(r, full_code, belongs_cache):
            rule_CUs = r.credits if r.credits else r.num
            if rule_CUs > priority_CUs:
                priority_rule = r
                priority_CUs = rule_CUs

    return priority_rule


def allocate_rules(
    full_code,
    rules_per_degree,
    rule_to_degree,
    double_counts,
    rule_selected=None,
    degree_plan=None,
    satisfied_rules=None,
    belongs_cache=None,
    graduate_sharing=None,
    credits_cache=None,
):
    """
    Given a course (full_code), rule, degree and double count mappings, and optionally a selected
    rule, degree plan, list of satisfied rules, and a belongs_cache (see prewarm_belongs_cache),
    returns rules (of all degrees in degreeplans) to show as selected by the course, rules to
    show as unselected, and if the selections are legal.
    """
    selected_rules = set()
    unselected_rules = set()
    if belongs_cache is None:
        belongs_cache = {}

    for degree in rules_per_degree:
        rules = rules_per_degree[degree].copy()
        if satisfied_rules is None:
            satisfied_rules = degree_plan.check_rules_already_satisfied(rules)

        # Find rule whose double counts we should consider. If we're in the right degree,
        # then it's rule_selected.
        chosen_rule = (
            rule_selected
            if rule_selected in rules
            else get_priority_rule(rules.difference(satisfied_rules), full_code, belongs_cache)
        )
        addl_selected_rules, addl_unselected_rules = assign_individual_rule(
            full_code,
            chosen_rule,
            rules,
            satisfied_rules,
            rule_to_degree,
            double_counts,
            belongs_cache,
        )

        selected_rules |= {
            rule for rule in addl_selected_rules if rule_to_degree.get(rule) == degree
        }
        unselected_rules |= {
            rule for rule in addl_unselected_rules if rule_to_degree.get(rule) == degree
        }

    # A submatriculant may only share so much between their two degrees, which the audit's own
    # ShareWith policy has no way of saying.
    if graduate_sharing is not None:
        selected_rules, unselected_rules = apply_graduate_sharing(
            full_code,
            selected_rules,
            unselected_rules,
            rule_to_degree,
            graduate_sharing,
            (credits_cache or {}).get(full_code, DEFAULT_COURSE_CREDITS),
        )

    # Check for illegal double counting
    legal = check_legal(selected_rules, rule_to_degree, double_counts)

    return selected_rules, unselected_rules, legal


def assign_individual_rule(
    full_code,
    chosen_rule,
    rules,
    satisfied_rules,
    rule_to_degree,
    double_counts,
    belongs_cache,
):
    """
    Given a course (full_code), a chosen rule, other rules, already satisfied rules, and the
    double counts allowed between rules, returns new sets of optimized selected and unselected
    rules relating to this full_code.
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
            if check_belongs(r, full_code, belongs_cache)
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
                else get_priority_rule(pick_one_rules, full_code, belongs_cache)
            )
            if picked_rule:
                selected_rules.add(picked_rule)
                rules.discard(picked_rule)

    # Consider all other rules within degree. If satisfies, add to unselected rules.
    # However, if full_code is listed and rule is currently unsatisfied, add
    # to satisfied rules (Intentionally should cause illegal double count)
    existing_degrees = [rule_to_degree.get(r) for r in selected_rules]
    for rule in rules:
        if full_code in rule.q and rule not in satisfied_rules:
            # check if this rule's degree is different from all degrees in selected_rules
            rule_degree = rule_to_degree.get(rule)
            if rule_degree not in existing_degrees:
                selected_rules.add(rule)
            else:
                unselected_rules.add(rule)
        elif check_belongs(rule, full_code, belongs_cache):
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

    The "degree" in the returned mappings is whatever contributed the rule -- a Degree, a
    Major or a Minor. The names are kept for the callers that already use them.
    """
    degree_trees = get_degree_trees(plan_components(degree_plan))

    rules_per_degree = defaultdict(set)
    rule_to_degree = {}
    for degree, rules in degree_trees.items():
        for rule in rules:
            if rule.q:  # i.e., if this rule is a leaf
                rules_per_degree[degree].add(rule)
                rule_to_degree[rule] = degree

    return rules_per_degree, rule_to_degree, resolve_double_counts(degree_trees)
