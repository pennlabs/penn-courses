"""
Which rules of a degree plan are allowed to share (i.e. double count) a course.

This policy is published by Path@Penn as `NONEXCLUSIVE` / `ShareWith` qualifiers on the
DegreeWorks audit, and `degree.utils.parse_path_audit` stores it on each rule as
`block_type`, `block_value` and `share_targets`. It used to be hand-written here as regexes
over rule titles, because the DegreeWorks JSON audit the old loader reads does not expose it.

Resolution happens at request time rather than being stored as resolved rule pairs, so newly
scraped degrees pick up their policy immediately with no seeding step to re-run.

A rule's `share_targets` name blocks, not rules:

    {"kind": "THISBLOCK"}                   other rules in its own block
    {"kind": "ANYBLOCK"}                    any other block; ours, standing for a block
                                            DegreeWorks marks STANDALONEBLOCK and so
                                            evaluates outside the degree's shared pool
    {"kind": "MAJOR"}                       any other block of that type
    {"kind": "OTHER", "value": "U-MT"}      that specific block
    {"kind": "MAJOR", "value": "AFRC"}      that specific major, since a major block's code
                                            is its major code

Rules with no targets may not double count with anything, which is DegreeWorks' default.

Note that this is symmetrical: if A names a block containing B, then B may share with A too,
whether or not B names A's block back.
"""

from collections import defaultdict
from itertools import permutations


THIS_BLOCK = "THISBLOCK"
ANY_BLOCK = "ANYBLOCK"


def get_degree_trees(degrees):
    """
    Maps each of the given degrees, majors or minors to all of its rules. Rules are fetched
    one level at a time, to avoid a query per rule.
    """
    trees = {}

    for owner in degrees:
        # owner.rules.model is Rule; referencing it this way avoids a circular import
        rule_model = owner.rules.model
        rules = list(owner.rules.all())

        level = rules
        while level:
            level = list(rule_model.objects.filter(parent__in=level))
            rules.extend(level)

        trees[owner] = rules

    return trees


def same_block(rule, other) -> bool:
    return (rule.block_type, rule.block_value) == (other.block_type, other.block_value)


def target_matches(target, home, other) -> bool:
    """
    Whether one of `home`'s share targets permits it to double count with `other`.

    Every kind but THISBLOCK names a *different* block: within a block, courses are exclusive
    unless THISBLOCK says otherwise. That reading is what makes THISBLOCK meaningful, but the
    audit does not state it, and it is the assumption everything here rests on.
    """
    kind, value = target.get("kind"), target.get("value")

    if kind == THIS_BLOCK:
        return same_block(home, other)
    if kind == ANY_BLOCK:
        return not same_block(home, other)
    if same_block(home, other) or kind != other.block_type:
        return False
    return value is None or value == other.block_value


def leaf_rules(degree_trees) -> list:
    """
    Every leaf rule of the given trees, deduplicated: rules are shared between degrees, so the
    same rule can appear in more than one tree.
    """
    return list(
        {rule.id: rule for rules in degree_trees.values() for rule in rules if rule.q}.values()
    )


def resolve_double_counts(degree_trees):
    """
    Given the rule trees of some degrees (as returned by get_degree_trees), returns a mapping
    from each of their leaf rules to the set of leaf rules it is allowed to double count with.
    """
    double_counts = defaultdict(set)

    for home, other in permutations(leaf_rules(degree_trees), 2):
        if any(target_matches(target, home, other) for target in home.share_targets):
            double_counts[home].add(other)
            double_counts[other].add(home)

    return dict(double_counts)
