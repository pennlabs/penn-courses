"""
What a plan is, once its degrees, majors and minors are taken together.

Each program is still its own rule tree. This module is the second pass: it classifies the
combination (one degree, a College double major, a cross-school dual, a coordinated program,
a submatriculation) and decides which trees are active and which sharing rules the audits
cannot state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from decimal import Decimal

from degree.models import (
    Degree,
    DegreePlan,
    graduate_programs,
    is_college,
    program_from_program_code,
)
from degree.utils.double_counts import get_degree_trees


logger = logging.getLogger(__name__)

MAJOR_BLOCK_TYPES = {"MAJOR", "CONC"}


@dataclass(eq=False)
class Component:
    """
    One unit of a plan that owns rules. Equality and hashing are the key only, so a
    component can be a dict key and still compare equal to the component `rule_to_component`
    records for the same key.
    """

    key: str
    relation: str
    owner_id: int | None
    role: str
    program: str | None
    title: str
    year: int | None
    is_graduate: bool
    is_college: bool
    counts_toward_degree_cap: bool
    removable: bool
    side: str | None
    rules: tuple
    roots: tuple
    extra_rules: tuple = ()
    keep_ids: frozenset = field(init=False)

    def __post_init__(self):
        self.rules = tuple(self.rules)
        self.roots = tuple(self.roots)
        self.extra_rules = tuple(self.extra_rules)
        self.keep_ids = frozenset(rule.id for rule in self.rules)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, Component) and self.key == other.key


@dataclass
class SharingPolicy:
    max_degree_claims: int = 2
    graduate_cu_limit: Decimal = Decimal(3)
    min_graduate_number: int = 5000
    forbid_grad_grad: bool = True
    cross_component_sharing: bool = False
    max_shared_cu: Decimal | None = None
    cas_double_major: bool = False


@dataclass
class Composition:
    kind: str
    components: list
    policy: SharingPolicy
    dual_program: object
    college_owner_id: int | None


class PlanRules:
    """
    The rule maps `allocate_rules` consumes, plus the composition that produced them.

    Iterating yields the historical triple so `rules, rule_to, counts = map_rules_and_degrees(plan)`
    keeps working.
    """

    def __init__(self, rules_per_component, rule_to_component, double_counts, composition):
        self.rules_per_component = rules_per_component
        self.rules_per_degree = rules_per_component
        self.rule_to_component = rule_to_component
        self.rule_to_degree = rule_to_component
        self.double_counts = double_counts
        self.composition = composition

    def __iter__(self):
        yield self.rules_per_component
        yield self.rule_to_component
        yield self.double_counts


def _leaves(rules):
    pending = list(rules)
    leaves = []
    while pending:
        rule = pending.pop()
        if rule.q:
            leaves.append(rule)
        else:
            pending.extend(list(rule.children.all()))
    return leaves


def _matcher_hits(rule, matcher) -> bool:
    block_type = matcher.get("block_type")
    block_value = matcher.get("block_value")
    needle = matcher.get("q_contains")
    if block_type and rule.block_type != block_type:
        return False
    if block_value and rule.block_value != block_value:
        return False
    if needle and needle not in (rule.q or ""):
        return False
    return bool(block_type or block_value or needle)


def apply_variant(leaves, variant):
    """
    Drop base leaves the variant suppresses and append the variant's own leaves.
    Returns (leaves, suppressed_ids, extra_roots).
    """
    if variant is None:
        return list(leaves), frozenset(), tuple()

    suppressed = []
    kept = []
    for rule in leaves:
        if any(_matcher_hits(rule, matcher) for matcher in variant.suppressed_rules):
            suppressed.append(rule)
        else:
            kept.append(rule)
    matched = {rule.id for rule in suppressed}
    for matcher in variant.suppressed_rules:
        if not any(_matcher_hits(rule, matcher) for rule in leaves):
            logger.warning("Variant %s matcher %s suppressed no rule.", variant.code, matcher)

    extra_roots = tuple(variant.rules.all())
    kept.extend(_leaves(extra_roots))
    return kept, frozenset(matched), extra_roots


def _degree_title(degree) -> str:
    name = degree.major_name or degree.major
    if degree.concentration_name:
        return f"{degree.degree} in {name} ({degree.concentration_name})"
    return f"{degree.degree} in {name}"


def _owner_rules(owner):
    trees = get_degree_trees([owner])
    rules = trees[owner]
    roots = list(owner.rules.all())
    return rules, roots


def _component_key(relation, owner_id) -> str:
    return f"{relation[:-1] if relation != 'degrees' else 'degree'}:{owner_id}"


def _base_component(owner, relation, role, program, cap=True) -> Component:
    rules, roots = _owner_rules(owner)
    return Component(
        key=_component_key(relation, owner.id),
        relation=relation,
        owner_id=owner.id,
        role=role,
        program=program,
        title=_title(owner, relation),
        year=getattr(owner, "year", None),
        is_graduate=program in graduate_programs,
        is_college=is_college(program),
        counts_toward_degree_cap=cap,
        removable=True,
        side=None,
        rules=[rule for rule in rules if rule.q],
        roots=roots,
    )


def _title(owner, relation) -> str:
    if relation == "degrees":
        return _degree_title(owner)
    if relation == "majors":
        name = owner.name or owner.code
        if owner.concentration_name:
            return f"Major in {name} ({owner.concentration_name})"
        return f"Major in {name}"
    return f"Minor in {owner.name or owner.code}"


def _side_owners(degree_plan, dual) -> dict[str, str]:
    """
    The component key that fills each side of a coordinated program.

    A side goes to one degree, or failing that one major, from that side's schools and
    allowed majors. The earliest added wins, since setting the program adds its pair first.
    A second degree or major from the same school, such as a second Wharton concentration,
    is an ordinary component: the program's variant and shared-CU cap do not apply to it.
    """
    candidates = [
        (_component_key("degrees", row.degree_id), row.degree.program, row.degree.major)
        for row in DegreePlan.degrees.through.objects.filter(degreeplan=degree_plan)
        .select_related("degree")
        .order_by("id")
    ] + [
        (
            _component_key("majors", row.major_id),
            program_from_program_code(row.major.program_code),
            row.major.code,
        )
        for row in DegreePlan.majors.through.objects.filter(degreeplan=degree_plan)
        .select_related("major")
        .order_by("id")
    ]
    sides = (
        ("left", dual.left_programs or [], dual.left_allowed_majors or []),
        ("right", dual.right_programs or [], dual.right_allowed_majors or []),
    )
    owners = {}
    for key, program, major in candidates:
        for side, programs, allowed in sides:
            if side in owners.values() or program not in programs:
                continue
            if allowed and major not in allowed:
                continue
            owners[key] = side
            break
    return owners


def _gather(degree_plan, dual) -> list[Component]:
    components = []
    for index, degree in enumerate(degree_plan.degrees.order_by("id")):
        role = "primary_degree" if index == 0 else "second_degree"
        components.append(_base_component(degree, "degrees", role, degree.program))
    for major in degree_plan.majors.order_by("id"):
        program = program_from_program_code(major.program_code)
        components.append(_base_component(major, "majors", "second_major", program))
    for minor in degree_plan.minors.order_by("id"):
        program = program_from_program_code(minor.program_code)
        components.append(_base_component(minor, "minors", "minor", program, cap=False))
    if dual is None:
        return components
    owners = _side_owners(degree_plan, dual)
    return [
        replace(component, side=owners[component.key]) if component.key in owners else component
        for component in components
    ]


def _variant_for(side, dual, override):
    if dual is None or side is None:
        return None
    if side == "right" and override is not None:
        return override
    return dual.left_variant if side == "left" else dual.right_variant


def _with_variant(component: Component, variant) -> Component:
    if variant is None:
        return component
    rules, _, extra = apply_variant(component.rules, variant)
    return replace(component, rules=rules, extra_rules=extra)


def _apply_variants(components, dual, override) -> list[Component]:
    return [
        _with_variant(component, _variant_for(component.side, dual, override))
        for component in components
    ]


def _split_college(components) -> list[Component]:
    """
    One College degree's general education, plus each College major's own block.
    A second College degree contributes its major block only.
    """
    primary = next(
        (component for component in components if component.relation == "degrees"),
        None,
    )
    split = []
    if primary is not None:
        college_leaves = [
            rule for rule in primary.rules if rule.block_type not in MAJOR_BLOCK_TYPES
        ]
        split.append(
            Component(
                key=f"college:{primary.owner_id}",
                relation="college",
                owner_id=primary.owner_id,
                role="college",
                program=primary.program,
                title="College requirements",
                year=primary.year,
                is_graduate=False,
                is_college=True,
                counts_toward_degree_cap=False,
                removable=False,
                side=None,
                rules=college_leaves,
                roots=primary.roots,
            )
        )
    for component in components:
        if component.relation == "degrees":
            major_leaves = [
                rule for rule in component.rules if rule.block_type in MAJOR_BLOCK_TYPES
            ]
            degree = Degree.objects.get(id=component.owner_id)
            split.append(
                Component(
                    key=f"degree-major:{component.owner_id}",
                    relation="degree-major",
                    owner_id=component.owner_id,
                    role="major",
                    program=component.program,
                    title=f"Major in {degree.major_name or degree.major}",
                    year=component.year,
                    is_graduate=False,
                    is_college=True,
                    counts_toward_degree_cap=True,
                    removable=True,
                    side=None,
                    rules=major_leaves,
                    roots=component.roots,
                )
            )
        else:
            split.append(component)
    return split


def _classify(components, dual) -> str:
    capped = [component for component in components if component.counts_toward_degree_cap]
    graduate = [component for component in capped if component.is_graduate]
    undergraduate = [component for component in capped if not component.is_graduate]
    if graduate and undergraduate:
        return "submatriculation"
    if dual is not None:
        return "coordinated"
    if len(undergraduate) >= 2 and all(component.is_college for component in undergraduate):
        return "cas_double_major"
    programs = {component.program for component in undergraduate}
    if len(undergraduate) >= 2 and len(programs) >= 2:
        return "cross_school_dual"
    return "single"


def _policy_for(kind, dual) -> SharingPolicy:
    return SharingPolicy(
        cross_component_sharing=kind != "single",
        max_shared_cu=getattr(dual, "max_shared_cu", None),
        cas_double_major=kind == "cas_double_major",
    )


def compose(degree_plan) -> Composition:
    dual = degree_plan.dual_program
    components = _gather(degree_plan, dual)
    kind = _classify(components, dual)
    if kind == "cas_double_major":
        components = _split_college(components)
    components = _apply_variants(components, dual, degree_plan.right_variant)
    return Composition(
        kind=kind,
        components=components,
        policy=_policy_for(kind, dual),
        dual_program=dual,
        college_owner_id=next(
            (component.owner_id for component in components if component.role == "college"),
            None,
        ),
    )
