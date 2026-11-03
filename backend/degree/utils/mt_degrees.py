"""
Degrees for the Jerome Fisher Program in Management & Technology (M&T), a coordinated dual degree
in Wharton (BS) and SEAS (BSE or BAS).

Path@Penn's public audits are what-if runs against a plain Wharton or plain SEAS student, so they
never show an M&T student's requirements:

  - The SEAS side switches to M&T versions of some rules when the student has two majors
    (`NUMMAJORS >= 2`), which `parse_path_audit` evaluates for an M&T degree. Its blocks are
    otherwise the public ones.
  - The Wharton side switches on `PROGRAM = WU_BS_MANT`, onto blocks the public audit does not
    contain at all. Those are kept in `degree/data/mt_wharton_blocks.json` and built here.

An M&T student's two degrees share one minimum total (46 CU) and may count a course toward both,
since DegreeWorks audits each degree separately.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.db.models import Q

from degree.models import Degree, Rule
from degree.utils.parse_path_audit import (
    MAX_TITLE_LENGTH,
    ParsedAudit,
    ParsedBlock,
    ShareTarget,
    any_of,
    apply_block_identity,
)
from degree.utils.programs import MT_PROGRAMS, MT_UNDECLARED_PROGRAM


MT_DATA = Path(__file__).resolve().parent.parent / "data" / "mt_wharton_blocks.json"

MT_UNDECLARED_MAJOR = "WUNG"
MT_UNDECLARED_MAJOR_NAME = "Wharton Undeclared"

# The Wharton blocks an M&T student meets instead of the public ones. The public audit's
# DEGREE and concentration (MAJOR) blocks still apply.
REPLACED_BLOCK_TYPES = {"OTHER"}

_data_cache = None


def mt_data() -> dict:
    global _data_cache
    if _data_cache is None:
        _data_cache = json.loads(MT_DATA.read_text())
    return _data_cache


def mt_total_credits() -> Decimal:
    return Decimal(str(mt_data()["total_credits"]))


def mt_variant(degree: Degree) -> Degree | None:
    """
    An unsaved M&T copy of an ordinary Wharton or SEAS degree, or None if the program has no
    M&T version.
    """
    program = MT_PROGRAMS.get(degree.program)
    if program is None:
        return None
    return Degree(
        program=program,
        degree=degree.degree,
        major=degree.major,
        major_name=degree.major_name,
        concentration=degree.concentration,
        concentration_name=degree.concentration_name,
    )


def mt_undeclared_degree() -> Degree:
    """An unsaved Wharton M&T degree for a student who has not chosen a concentration."""
    return Degree(
        program=MT_UNDECLARED_PROGRAM,
        degree="BS",
        major=MT_UNDECLARED_MAJOR,
        major_name=MT_UNDECLARED_MAJOR_NAME,
    )


def course_q(spec: dict) -> Q:
    """The courses one rule spec accepts: listed courses, attributes and whole departments."""
    accepted = []
    if spec.get("courses"):
        accepted.append(Q(full_code__in=spec["courses"]))
    if spec.get("attributes"):
        accepted.append(Q(attributes__code__in=spec["attributes"]))
    if spec.get("departments"):
        accepted.append(Q(department__code__in=spec["departments"]))
    return any_of(accepted)


def find_public_rule(public: ParsedAudit, title: str) -> Rule:
    """
    A leaf rule of the public audit by title. Rules M&T shares with plain Wharton are taken
    from there, so they stay as current as the rest of the import.
    """
    matches = [rule for rule in public.rules if rule.q and rule.title == title]
    if not matches:
        raise LookupError(f"M&T rule {title!r} not found in the public Wharton audit")
    return matches[0]


def build_rule(spec: dict, parent: Rule, public: ParsedAudit) -> list[Rule]:
    """The rules one spec contributes, parents before children."""
    title = spec["title"][:MAX_TITLE_LENGTH]

    if "from_public" in spec:
        source = find_public_rule(public, spec["from_public"])
        rule = Rule(
            parent=parent,
            title=title,
            q=source.q,
            num=source.num,
            credits=source.credits,
            share_targets=[],
        )
        return [rule]

    if "rules" in spec:
        rule = Rule(parent=parent, title=title, share_targets=[])
        children = [r for child in spec["rules"] for r in build_rule(child, rule, public)]
        return [rule, *children]

    q = course_q(spec)
    if not q:
        raise ValueError(f"M&T rule {title!r} accepts no courses")
    return [
        Rule(
            parent=parent,
            title=title,
            q=repr(q),
            num=spec.get("num"),
            credits=spec.get("credits"),
            share_targets=[],
        )
    ]


def build_block(spec: dict, public: ParsedAudit) -> tuple[ParsedBlock, list[Rule]]:
    root = Rule(title=spec["title"][:MAX_TITLE_LENGTH], share_targets=[])
    rules = [root, *(r for rule in spec["rules"] for r in build_rule(rule, root, public))]
    block = ParsedBlock(
        req_type="OTHER",
        req_value=spec["req_value"],
        title=spec["title"],
        credits=Decimal(str(spec["credits"])),
        catalog_year=public.catalog_year,
        root_rule=root,
        share_targets=[ShareTarget(t["kind"], t.get("value")) for t in spec["share_targets"]],
    )
    apply_block_identity(rules, block)
    return block, rules


def mt_wharton_audit(
    as_mt: ParsedAudit, as_plain: ParsedAudit, keep_major: bool = True
) -> ParsedAudit:
    """
    The Wharton side of M&T.

    `as_mt` is a public Wharton audit parsed for the M&T degree. Its DEGREE block, and its
    concentration block when `keep_major`, are kept, and its OTHER blocks are replaced by the
    M&T ones.

    `as_plain` is the same audit parsed for the plain Wharton degree, which is where rules M&T
    shares with plain Wharton are taken from: under the M&T program the audit's conditions can
    select branches the public audit does not contain.
    """
    kept = [
        block
        for block in as_mt.blocks
        if block.req_type not in REPLACED_BLOCK_TYPES and (keep_major or block.req_type != "MAJOR")
    ]
    kept_ids = {(block.req_type, block.req_value) for block in kept}
    kept_rules = [rule for rule in as_mt.rules if (rule.block_type, rule.block_value) in kept_ids]

    built = [build_block(spec, as_plain) for spec in mt_data()["blocks"]]
    return ParsedAudit(
        degree_credits=mt_total_credits(),
        catalog_year=as_mt.catalog_year,
        rules=[*kept_rules, *(rule for _, rules in built for rule in rules)],
        blocks=[*kept, *(block for block, _ in built)],
    )


def mt_seas_audit(parsed: ParsedAudit) -> ParsedAudit:
    """The SEAS side of M&T: the public audit parsed for an M&T degree, at the M&T total."""
    parsed.degree_credits = mt_total_credits()
    return parsed
