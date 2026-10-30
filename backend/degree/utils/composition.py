"""
What a plan is, once its degrees, majors and minors are taken together.

Each program is still its own rule tree. This module is the second pass: it classifies the
combination (one degree, a College double major, a cross-school dual, a coordinated program,
a submatriculation) and decides which trees are active and which sharing rules the audits
cannot state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from degree.models import Degree, graduate_programs, is_college, program_from_program_code
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
    keep_ids: frozenset
    extra_rules: tuple

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


def _make(
    key,
    relation,
    owner_id,
    role,
    program,
    title,
    year,
    graduate,
    college,
    cap,
    removable,
    side,
    leaves,
    roots,
    suppressed,
    extra,
) -> Component:
    kept = tuple(rule for rule in leaves if rule.id not in suppressed)
    return Component(
        key=key,
        relation=relation,
        owner_id=owner_id,
        role=role,
        program=program,
        title=title,
        year=year,
        is_graduate=graduate,
        is_college=college,
        counts_toward_degree_cap=cap,
        removable=removable,
        side=side,
        rules=kept,
        roots=tuple(roots),
        keep_ids=frozenset(rule.id for rule in kept),
        extra_rules=tuple(extra),
    )


def _owner_rules(owner):
    trees = get_degree_trees([owner])
    rules = trees[owner]
    roots = list(owner.rules.all())
    return rules, roots


def _base_component(owner, relation, role, program, side, cap=True) -> Component:
    rules, roots = _owner_rules(owner)
    leaves = [rule for rule in rules if rule.q]
    graduate = program in graduate_programs
    return _make(
        key=f"{relation[:-1] if relation != 'degrees' else 'degree'}:{owner.id}",
        relation=relation,
        owner_id=owner.id,
        role=role,
        program=program,
        title=_title(owner, relation),
        year=getattr(owner, "year", None),
        graduate=graduate,
        college=is_college(program),
        cap=cap,
        removable=True,
        side=side,
        leaves=leaves,
        roots=roots,
        suppressed=frozenset(),
        extra=(),
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


def _side_for(program, dual) -> str | None:
    if dual is None or program is None:
        return None
    if program in (dual.left_programs or []):
        return "left"
    if program in (dual.right_programs or []):
        return "right"
    return None


def _variant_for(side, dual, override):
    if dual is None or side is None:
        return None
    if side == "right" and override is not None:
        return override
    return dual.left_variant if side == "left" else dual.right_variant


def _with_variant(component: Component, variant) -> Component:
    if variant is None:
        return component
    leaves, suppressed, extra = apply_variant(component.rules, variant)
    return _make(
        key=component.key,
        relation=component.relation,
        owner_id=component.owner_id,
        role=component.role,
        program=component.program,
        title=component.title,
        year=component.year,
        graduate=component.is_graduate,
        college=component.is_college,
        cap=component.counts_toward_degree_cap,
        removable=component.removable,
        side=component.side,
        leaves=leaves,
        roots=component.roots,
        suppressed=suppressed,
        extra=extra,
    )


def _is_cas_double_major(components, dual) -> bool:
    if dual is not None:
        return False
    capped = [component for component in components if component.counts_toward_degree_cap]
    return len(capped) >= 2 and all(
        component.is_college and not component.is_graduate for component in capped
    )


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
            _make(
                key=f"college:{primary.owner_id}",
                relation="college",
                owner_id=primary.owner_id,
                role="college",
                program=primary.program,
                title="College requirements",
                year=primary.year,
                graduate=False,
                college=True,
                cap=False,
                removable=False,
                side=None,
                leaves=college_leaves,
                roots=primary.roots,
                suppressed=frozenset(),
                extra=(),
            )
        )
    for component in components:
        if component.relation == "degrees":
            major_leaves = [
                rule for rule in component.rules if rule.block_type in MAJOR_BLOCK_TYPES
            ]
            degree = Degree.objects.get(id=component.owner_id)
            split.append(
                _make(
                    key=f"degree-major:{component.owner_id}",
                    relation="degree-major",
                    owner_id=component.owner_id,
                    role="major",
                    program=component.program,
                    title=f"Major in {degree.major_name or degree.major}",
                    year=component.year,
                    graduate=False,
                    college=True,
                    cap=True,
                    removable=True,
                    side=None,
                    leaves=major_leaves,
                    roots=component.roots,
                    suppressed=frozenset(),
                    extra=(),
                )
            )
        else:
            split.append(component)
    return split


def _kind(components, dual) -> str:
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


def compose(degree_plan) -> Composition:
    dual = degree_plan.dual_program
    override = degree_plan.right_variant

    raw = []
    degrees = list(degree_plan.degrees.order_by("id"))
    for index, degree in enumerate(degrees):
        role = "primary_degree" if index == 0 else "second_degree"
        raw.append(
            _base_component(
                degree, "degrees", role, degree.program, _side_for(degree.program, dual)
            )
        )
    for major in degree_plan.majors.order_by("id"):
        program = program_from_program_code(major.program_code)
        raw.append(
            _base_component(major, "majors", "second_major", program, _side_for(program, dual))
        )
    for minor in degree_plan.minors.order_by("id"):
        program = program_from_program_code(minor.program_code)
        raw.append(_base_component(minor, "minors", "minor", program, None, cap=False))

    if _is_cas_double_major(raw, dual):
        raw = _split_college(raw)

    components = [
        _with_variant(component, _variant_for(component.side, dual, override)) for component in raw
    ]
    kind = _kind(components, dual)
    policy = SharingPolicy(
        cross_component_sharing=kind != "single",
        max_shared_cu=getattr(dual, "max_shared_cu", None),
        cas_double_major=kind == "cas_double_major",
    )
    college_owner_id = next(
        (component.owner_id for component in components if component.role == "college"), None
    )
    return Composition(
        kind=kind,
        components=components,
        policy=policy,
        dual_program=dual,
        college_owner_id=college_owner_id,
    )
