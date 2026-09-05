"""
Which rules of a degree are allowed to share (i.e. double count) a course.

DegreeWorks doesn't publish this policy, so it is hand-written here as patterns over rule
titles, and resolved against a degree's actual rules at request time. Resolving at request
time (rather than storing the resolved rule pairs in the database) means newly scraped
degrees pick up the policy immediately, with no seeding step to re-run.

Each entry reads: every leaf rule under `home_rule` may double count with every leaf rule
under each of `allow_double_count` (or with every leaf rule of the degree, for "ALL_RULES").
`home_rule` and the `allow_double_count` patterns are regexes matched against rule titles
with `re.match`, and every matching rule is used (a degree can have several, e.g. the
"Area List - ___" rules). A rule that is itself a leaf counts as its own leaf, so patterns
can name either a parent rule or the leaves directly.

Note that this is symmetrical: if A may double count with B, then B may double count with A.
"""

import re
from collections import defaultdict


# The kinds of block a rule's share targets can name. THISBLOCK is DegreeWorks'
# own word; ANYBLOCK is ours, for a block marked STANDALONEBLOCK and so evaluated
# outside the degree's shared pool of courses.
THIS_BLOCK = "THISBLOCK"
ANY_BLOCK = "ANYBLOCK"


DOUBLE_COUNT_ENTRIES = [
    # ===College===
    {
        "type": "BA",
        "major_code": "ALL_MAJORS",
        "home_rule": "General Education, Foundations",
        "allow_double_count": ["General Education, Sectors", r"^Major in\b"],
    },
    # ===Engineering===
    # CIS BSE: area lists and concentrations double count with anything in the degree.
    # Degrees before 2026 use the "CSCI" major code and group their area lists under an
    # "AREA LISTS" rule; newer ones use "CIS" and have "Area List - ___" leaf rules.
    {
        "type": "BSE",
        "major_code": "CSCI",
        "home_rule": "AREA LISTS",
        "allow_double_count": ["ALL_RULES"],
    },
    {
        "type": "BSE",
        "major_code": "CSCI",
        "home_rule": r"^Concentration in\b",
        "allow_double_count": ["ALL_RULES"],
    },
    {
        "type": "BSE",
        "major_code": "CIS",
        "home_rule": r"^Area List\b",
        "allow_double_count": ["ALL_RULES"],
    },
    {
        "type": "BSE",
        "major_code": "CIS",
        "home_rule": r"^Concentration in\b",
        "allow_double_count": ["ALL_RULES"],
    },
    # ===Wharton===
]


def get_degree_trees(degrees):
    """
    Returns a mapping from each of the given degrees to its rule tree, as a tuple of all the
    degree's rules and a mapping from rule id to child rules. Rules are fetched one level at a
    time, to avoid a query per rule.
    """
    degree_trees = {}

    for degree in degrees:
        # degree.rules.model is Rule; referencing it this way avoids a circular import
        rule_model = degree.rules.model
        children = defaultdict(list)
        rules = list(degree.rules.all())

        level = list(rules)
        while level:
            level = list(rule_model.objects.filter(parent__in=level))
            rules.extend(level)
            for rule in level:
                children[rule.parent_id].append(rule)

        degree_trees[degree] = (rules, children)

    return degree_trees


def get_leaves(rule, children):
    """
    Returns the leaf rules (i.e., the rules with a q object, which are the only rules a course
    can actually fulfill) belonging to the given rule. A leaf rule belongs to itself.
    """
    if rule.q:
        return {rule}

    leaves = set()
    stack = [rule]
    while stack:
        for child in children[stack.pop().id]:
            if child.q:
                leaves.add(child)
            else:
                stack.append(child)
    return leaves


def matching_leaves(pattern, rules, children):
    """
    Returns the leaf rules belonging to every rule whose title matches the given pattern.
    """
    return {
        leaf
        for rule in rules
        if re.match(pattern, rule.title)
        for leaf in get_leaves(rule, children)
    }


def resolve_double_counts(degree_trees):
    """
    Given the rule trees of some degrees (as returned by get_degree_trees), returns a mapping
    from each of their leaf rules to the set of leaf rules it is allowed to double count with,
    per DOUBLE_COUNT_ENTRIES.
    """
    double_counts = defaultdict(set)

    for degree, (rules, children) in degree_trees.items():
        entries = [
            entry
            for entry in DOUBLE_COUNT_ENTRIES
            if entry["type"] == degree.degree
            and entry["major_code"] in (degree.major, "ALL_MAJORS")
        ]
        if not entries:
            continue

        all_leaves = {rule for rule in rules if rule.q}
        for entry in entries:
            home_leaves = matching_leaves(entry["home_rule"], rules, children)
            if not home_leaves:
                continue

            for allow_double_count in entry["allow_double_count"]:
                if allow_double_count == "ALL_RULES":
                    target_leaves = all_leaves
                else:
                    target_leaves = matching_leaves(allow_double_count, rules, children)

                for home_leaf in home_leaves:
                    double_counts[home_leaf] |= target_leaves - {home_leaf}
                for target_leaf in target_leaves:
                    double_counts[target_leaf] |= home_leaves - {target_leaf}

    return dict(double_counts)
