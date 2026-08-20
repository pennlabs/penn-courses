import re
from collections import defaultdict, deque

from django.db.models import Q

from courses.models import Course
from degree.utils.double_counts import get_degree_trees, resolve_double_counts


def aggregate_rule_leaves(rules, f):
    """
    Given a list of rules and a function f,
    performs f on each leaf rule.
    """
    bfs_queue = deque()
    bfs_queue.extend(rules)
    while bfs_queue:
        for child in bfs_queue.pop().children.all():
            if child.q:  # i.e., if this child is a leaf
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
        if not rule.q:  # only leaf rules can be checked with a single query
            continue
        matched = set(
            Course.objects.filter(rule.get_q_object() or Q(), full_code__in=full_codes).values_list(
                "full_code", flat=True
            )
        )
        for full_code in full_codes:
            belongs_cache[(rule.id, full_code)] = full_code in matched

    return belongs_cache


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
        selected_rules = selected_rules.union(addl_selected_rules)
        unselected_rules = unselected_rules.union(addl_unselected_rules)

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
    """
    for rule in selected_rules:
        degree = rule_to_degree.get(rule)
        if degree is None:  # not a leaf rule of any degree in the plan (e.g. an override)
            continue
        allowed = double_counts.get(rule, set())
        if any(
            r not in allowed and rule_to_degree.get(r) == degree and r != rule
            for r in selected_rules
        ):
            return False
    return True


def map_rules_and_degrees(degree_plan):
    """
    Given a degree plan, produces mappings of rules to degrees, and of each rule to the rules
    it is allowed to double count with.
    """
    degree_trees = get_degree_trees(degree_plan.degrees.all())

    rules_per_degree = defaultdict(set)
    rule_to_degree = {}
    for degree, (rules, _) in degree_trees.items():
        for rule in rules:
            if rule.q:  # i.e., if this rule is a leaf
                rules_per_degree[degree].add(rule)
                rule_to_degree[rule] = degree

    return rules_per_degree, rule_to_degree, resolve_double_counts(degree_trees)
