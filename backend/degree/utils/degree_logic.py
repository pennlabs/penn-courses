import re
from collections import defaultdict, deque


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


def get_priority_rule(rules, full_code):
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

        if r.check_belongs(full_code):
            rule_CUs = r.credits if r.credits else r.num
            if rule_CUs > priority_CUs:
                priority_rule = r
                priority_CUs = rule_CUs

    return priority_rule


def allocate_rules(
    full_code,
    rules_per_degree,
    rule_to_degree,
    rule_selected=None,
    degree_plan=None,
    satisfied_rules=None,
):
    """
    Given a course (full_code), rule and degree mappings, and optionally a selected rule, degree
    plan, and list of satisfied rules, returns rules (of all degrees in degreeplans) to show as
    selected by the course, rules to show as unselected, and if the selections are legal.
    """
    selected_rules = set()
    unselected_rules = set()

    for degree in rules_per_degree:
        rules = rules_per_degree[degree].copy()
        if satisfied_rules is None:
            satisfied_rules = degree_plan.check_rules_already_satisfied(rules)

        # Find rule whose double counts we should consider. If we're in the right degree,
        # then it's rule_selected.
        chosen_rule = (
            rule_selected
            if rule_selected in rules
            else get_priority_rule(rules.difference(satisfied_rules), full_code)
        )
        addl_selected_rules, addl_unselected_rules = assign_individual_rule(
            full_code, chosen_rule, rules, satisfied_rules
        )
        selected_rules = selected_rules.union(addl_selected_rules)
        unselected_rules = unselected_rules.union(addl_unselected_rules)

    # Check for illegal double counting
    legal = check_legal(selected_rules, rule_to_degree)

    return selected_rules, unselected_rules, legal


def assign_individual_rule(full_code, chosen_rule, rules, satisfied_rules):
    """
    Given a course (full_code), a chosen rule, other rules, and already satisfied rules,
    returns new sets of optimized selected and unselected rules relating to this full_code.
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
            r for r in chosen_rule.can_double_count_with.all() if r.check_belongs(full_code)
        }
        relevant_dcrs.add(chosen_rule)

        mutual_rules = relevant_dcrs.copy()
        pick_one_rules = set()
        for r1 in relevant_dcrs:
            for r2 in relevant_dcrs:
                if r2 not in r1.can_double_count_with.all():
                    mutual_rules.discard(r2)
                    pick_one_rules.add(r2)

        selected_rules = selected_rules.union(mutual_rules)
        rules.difference_update(mutual_rules)

        # Pick one of the pick_one_rules (if not chosen rule, it's random right now)
        if len(pick_one_rules):
            picked_rule = (
                chosen_rule
                if chosen_rule in pick_one_rules
                else get_priority_rule(pick_one_rules, full_code)
            )
            selected_rules.add(picked_rule)
            # TODO: We use .discard() because can_double_count_with contains rules
            # that AREN'T leaf rules. (ex. BREADTH REQUIREMENTS for Cog Sci Major). Fix!
            rules.discard(picked_rule)

    # Consider all other rules within degree. If satisfies, add to unselected rules.
    # However, if full_code is listed and rule is currently unsatisfied, add
    # to satisfied rules (Intentionally should cause illegal double count)
    for rule in rules:
        if full_code in rule.q and rule not in satisfied_rules:
            selected_rules.add(rule)
        elif rule.check_belongs(full_code):
            unselected_rules.add(rule)

    return selected_rules, unselected_rules


def check_legal(selected_rules, rule_to_degree):
    """
    Given a list of selected rules and rule to degree mappings, returns True if all selected rules
    can be double counter with each other and False otherwise.
    """
    for rule in selected_rules:
        if any(
            r not in rule.can_double_count_with.all()
            and rule_to_degree[r] == rule_to_degree[rule]
            and r != rule
            for r in selected_rules
        ):
            return False
    return True


def map_rules_and_degrees(degree_plan):
    """
    Given a degree plan, produces mappings of rules to degrees.
    """
    rules_per_degree = defaultdict(set)
    rule_to_degree = {}

    for degree in degree_plan.degrees.all():

        def on_child_rule(curr_rule):
            rules_per_degree[degree].add(curr_rule)
            rule_to_degree[curr_rule] = degree

        aggregate_rule_leaves(degree.rules.all(), on_child_rule)

    return rules_per_degree, rule_to_degree
