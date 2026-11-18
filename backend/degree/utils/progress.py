"""
How far along each of a plan's degrees, majors and minors is, as the requirements panel shows
it: a requirement counts the courses placed on it toward what it asks for, a group its furthest
children up to how many it asks for, and a program the average of its top-level requirements.
"""

from collections import defaultdict

from degree.utils.composition import compose
from degree.utils.degree_logic import prewarm_credits_cache, rule_subtrees


def _programs(plan):
    """(relation, program, top-level rules, ids of the leaves it keeps or None) per program."""
    changed = {}
    if plan.dual_program_id is not None:
        # A coordinated program (e.g. M&T) replaces some of its programs' requirements.
        for component in compose(plan).components:
            changed[(component.relation, component.owner_id)] = component
    for relation in ("degrees", "majors", "minors"):
        for program in getattr(plan, relation).all():
            component = changed.get((relation, program.id))
            if component is None:
                yield relation, program, list(program.rules.all()), None
            else:
                roots = [*component.roots, *component.extra_rules]
                keep = component.keep_ids | {rule.id for rule in component.extra_rules}
                yield relation, program, roots, keep


def plan_progress(plans):
    """{plan id: {(relation, program id): a fraction from 0 to 1}} for the given plans."""
    programs = {plan.id: list(_programs(plan)) for plan in plans}
    children = defaultdict(list)
    for rule in rule_subtrees(
        rule for listed in programs.values() for *_, roots, _ in listed for rule in roots
    ):
        if rule.parent_id is not None:
            children[rule.parent_id].append(rule)

    full_codes = {f.full_code for plan in plans for f in plan.fulfillments.all()}
    credits = prewarm_credits_cache(full_codes)

    progress = {}
    for plan in plans:
        waived = {rule.id for rule in plan.waived_rules.all()}
        placed = defaultdict(list)
        for fulfillment in plan.fulfillments.all():
            for rule in fulfillment.rules.all():
                placed[rule.id].append(float(credits.get(fulfillment.full_code) or 1))

        def rule_progress(rule, keep):
            if rule.q:
                if rule.id in waived:
                    return 1
                courses = placed[rule.id]
                return min(
                    1,
                    sum(courses) / float(rule.credits) if rule.credits else 1,
                    len(courses) / rule.num if rule.num else 1,
                )
            kept = [child for child in children[rule.id] if is_kept(child, keep)]
            required = min(len(kept), rule.num or len(kept))
            if not required:
                return 0
            furthest = sorted((rule_progress(child, keep) for child in kept), reverse=True)
            return sum(furthest[:required]) / required

        def is_kept(rule, keep):
            if keep is None:
                return True
            if rule.q:
                return rule.id in keep
            return any(is_kept(child, keep) for child in children[rule.id])

        progress[plan.id] = {
            (relation, program.id): (
                sum(rule_progress(rule, keep) for rule in kept) / len(kept)
                if (kept := [rule for rule in roots if is_kept(rule, keep)])
                else 0
            )
            for relation, program, roots, keep in programs[plan.id]
        }
    return progress
