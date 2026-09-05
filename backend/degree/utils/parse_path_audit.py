"""
Parses the DegreeWorks audit XML that Path@Penn serves (see `degree.utils.path_client`).

This is the same data model as the DegreeWorks JSON audit that `parse_degreeworks` reads, in a
different serialization -- the RuleType values are identical -- so the two modules are laid out
the same way and can be diffed against each other. The XML is strictly richer than the JSON:

  - `<Except>` nodes give the courses a rule explicitly does NOT accept, which the JSON audit
    does not expose and `parse_degreeworks` therefore drops.
  - `NONEXCLUSIVE` qualifiers give the double-count policy, which `degree.utils.double_counts`
    used to hand-encode as regexes over rule titles.
  - The DEGREE block gives the degree's total credit requirement directly, rather than via a
    string match on a qualifier label.
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal
from functools import reduce
from operator import and_, or_

from django.db.models import Q

from courses.util import semester_suffix_map_hum, translate_semester_inv
from degree.models import Degree, Rule
from degree.utils.departments import ENG_DEPTS, SAS_DEPTS, WH_DEPTS
from degree.utils.double_counts import ANY_BLOCK, THIS_BLOCK


logger = logging.getLogger(__name__)

# DegreeWorks also emits block types we have no model for.
BLOCK_TYPES = frozenset({"DEGREE", "MAJOR", "MINOR", "CONC", "OTHER"})

# Rule types that carry no requirement of their own: headings, and rules the audit has already
# settled.
IGNORED_RULE_TYPES = frozenset({"Complete", "Incomplete", "Noncourse", "Block", "Blocktype"})

# Restrictions that are not properties of a course in our catalog.
IGNORED_WITH_CODES = frozenset({"DWRESIDENT", "DWGRADE", "DWCOURSENUMBER", "DWPASSFAIL", "DWAGE"})

COLLEGE_DEPARTMENTS = {
    "E": ENG_DEPTS,
    "EU": ENG_DEPTS,
    "A": SAS_DEPTS,
    "AU": SAS_DEPTS,
    "W": WH_DEPTS,
    "WU": WH_DEPTS,
}

SEASON_SUFFIXES = {season: suffix for suffix, season in semester_suffix_map_hum.items()}
SEMESTER_CODE = re.compile(r"^\d{4}[ABC]$")
WITH_CLAUSE = re.compile(r"\(With .*?\)")

MAX_TITLE_LENGTH = Rule._meta.get_field("title").max_length


@dataclass(frozen=True)
class ShareTarget:
    """
    One target of a `ShareWith` (NONEXCLUSIVE) qualifier: what a rule may double count with.

    `kind` is a block type -- MAJOR, MINOR, CONC, OTHER -- or THISBLOCK. `value` is the
    specific block or major code when the qualifier names one, as in `(OTHER = U-SEAS-WREE)`
    or `(MAJOR = AFRC)`, and None when it names a whole type, as in `(MAJOR)`.
    """

    kind: str
    value: str | None = None

    def as_dict(self) -> dict:
        return {"kind": self.kind, "value": self.value}


@dataclass
class ParsedBlock:
    """One requirement block of an audit, and the rules parsed out of it."""

    req_type: str
    req_value: str
    title: str
    credits: Decimal | None
    catalog_year: int | None
    root_rule: Rule | None
    share_targets: list[ShareTarget] = field(default_factory=list)


@dataclass
class ParsedAudit:
    """
    The result of parsing one program's audit. Rules are built but not saved.
    """

    degree_credits: Decimal | None
    catalog_year: int | None
    rules: list[Rule]
    blocks: list[ParsedBlock]


def text_of(element) -> str:
    return (element.text or "").strip() if element is not None else ""


def subtext_of(element) -> str:
    return " ".join(text_of(sub) for sub in element.findall("SubText")).strip()


def qualifiers(block, *names):
    """The header qualifiers of a block with any of the given names."""
    header = block.find("Header")
    if header is None:
        return []
    return [q for q in header.findall("Qualifier") if q.get("Name") in names]


def any_of(qs) -> Q:
    return reduce(or_, qs, Q())


def all_of(qs) -> Q:
    return reduce(and_, qs, Q())


def unique(items: list) -> list:
    """Deduplicates while preserving order."""
    return list(dict.fromkeys(items))


def parse_with(with_element) -> Q | None:
    """
    A Q filter for one `<With>` restriction on a course, or None if the restriction cannot
    apply to a catalog course -- in which case the course it restricts is dropped.
    """
    code = with_element.get("Code")
    values = [text_of(value) for value in with_element.findall("Value")]

    if code in IGNORED_WITH_CODES:
        logger.info(f"ignoring With restriction {code}")
        return Q()

    match code:
        # DWATTR carries course attribute codes just as ATTRIBUTE does. Ignoring it, as
        # parse_degreeworks does, widens the rule to every course in the department.
        case "ATTRIBUTE" | "DWATTR":
            return Q(attributes__code__in=values)
        case "DWCOLLEGE":
            if len(values) != 1:
                raise LookupError(f"Expected one college in With, got {values}")
            if values[0] not in COLLEGE_DEPARTMENTS:
                raise ValueError(f"Unsupported college in With: {values[0]}")
            return Q(department__code__in=COLLEGE_DEPARTMENTS[values[0]])
        case "DWTERM":
            return parse_terms(values, with_element.get("Operator"))
        # AP/IB/transfer equivalencies, which never name a catalog course.
        case "DWTRANSFERSCHOOLID":
            return None
        case _:
            raise LookupError(f"Unknown With code: {code}")


def parse_term(value: str) -> str | None:
    """
    One DWTERM value as a semester code, or None if unreadable. DegreeWorks writes terms
    either in words ("Spring 2020") or as Path term codes ("202010"), both meaning 2020A.
    """
    match value.split():
        case [season, year] if season in SEASON_SUFFIXES and year.isdigit():
            return f"{year}{SEASON_SUFFIXES[season]}"
        case [token] if SEMESTER_CODE.match(token):
            return token
        case [token] if SEMESTER_CODE.match(translate_semester_inv(token, ignore_error=True)):
            return translate_semester_inv(token)

    logger.warning(f"Unexpected DWTERM value: {value!r}")
    return None


def parse_terms(values: list[str], operator: str | None) -> Q:
    """
    A DWTERM restriction, which names one or more terms and compares against them with the
    With's operator. Several terms at once is normal: the COVID pass/fail carve-outs list
    "Spring 2020", "Summer 2020", "Fall 2020" and "Spring 2021" together.

    A restriction we cannot read is ignored rather than narrowing the rule to nothing.
    """
    semesters = sorted(filter(None, map(parse_term, values)))
    if not semesters:
        logger.warning(f"No usable terms in DWTERM {values}; ignoring restriction")
        return Q()

    earliest, latest = semesters[0], semesters[-1]
    match operator:
        case "=" | "" | None:
            return Q(semester__in=semesters)
        case "<>":
            return ~Q(semester__in=semesters)
        case "<":
            return Q(semester__lt=earliest)
        case "<=":
            return Q(semester__lte=latest)
        case ">":
            return Q(semester__gt=latest)
        case ">=":
            return Q(semester__gte=earliest)
        case _:
            logger.warning(f"Unknown DWTERM operator {operator!r}; ignoring restriction")
            return Q()


def parse_course(course_element) -> Q | None:
    """
    A Q filter matching the courses one `<Course>` node accepts, or None if it cannot match
    any catalog course. An `@` stands for any discipline or any number.
    """
    discipline = course_element.get("Disc")
    number = course_element.get("Num")
    number_end = course_element.get("Num_end")

    match (discipline, number, number_end):
        case ("@" | "PSEUDO@", "@", None):
            course_q = Q()
        case (discipline, "@", None):
            course_q = Q(department__code=discipline)
        case ("@", number, None):
            course_q = Q() if "@" in number else Q(code=number)
        case (discipline, number, None) if "@" not in number:
            course_q = Q(full_code=f"{discipline}-{number}")
        case (discipline, number, None) if number[:-1].isdigit() and number.endswith("@"):
            course_q = Q(full_code__startswith=f"{discipline}-{number[:-1]}")
        case ("@", number, end):
            course_q = Q(code__gte=number.strip(), code__lte=end.strip())
        case (discipline, number, end):
            course_q = Q(
                department__code=discipline, code__gte=number.strip(), code__lte=end.strip()
            )
        case _:
            course_q = Q()

    # A With's connector joins it to the *next* With, so it is carried forward.
    connector = "AND"
    for with_element in course_element.findall("With"):
        restriction = parse_with(with_element)
        if restriction is None:
            return None
        match connector:
            case "AND" | "":
                course_q &= restriction
            case "OR":
                course_q |= restriction
            case _:
                raise LookupError(f"Unknown With connector: {connector}")
        connector = with_element.get("Connector") or "AND"

    return course_q or None


def parse_requirement_courses(requirement) -> Q:
    """
    The courses a `<Requirement>` accepts, less anything named under its `<Except>` node.

    A Connector of "," lists alternatives and "AND" requires all of them. A leaf Rule is a
    single Q plus a count, so an AND of distinct courses collapses to a filter no course
    satisfies; parse_degreeworks has the same limitation, and the warning below marks it.
    """
    accepted = list(filter(None, map(parse_course, requirement.findall("Course"))))
    requires_all = requirement.get("Connector") == "AND"
    q = all_of(accepted) if requires_all else any_of(accepted)

    if requires_all and len(q) > 1:
        logger.warning(f"AND-connected course list is unsatisfiable: {q}")

    excluded = any_of(filter(None, map(parse_course, requirement.findall("Except/Course"))))
    if excluded:
        q &= ~excluded

    if not q:
        logger.warning("empty course query")
    return q


def parse_course_list(text: str) -> Q:
    """
    The shorthand course list a qualifier carries in its SubText, e.g.
    "NETS 1500, 2120, CIS 4510, 5510" or "AAMW @, AFRC @" or "MED 0000:9999".

    A discipline carries forward until a new one appears, so "NETS 1500, 2120" means NETS 1500
    and NETS 2120. `@` in place of a number means any course in that discipline, and a colon
    separates an inclusive range.
    """
    full_codes, departments, codes, ranges = [], [], [], []
    discipline = None

    for token in WITH_CLAUSE.sub("", text).split(","):
        match token.split():
            case [discipline, number]:
                pass
            case [number]:
                pass
            case []:
                continue
            case parts:
                logger.warning(f"Unexpected token in course list: {parts}")
                continue

        if discipline is None:
            logger.warning(f"Course list starts without a discipline: {text!r}")
            continue

        if discipline == "@":
            if number != "@":
                codes.append(number)
        elif number == "@":
            departments.append(discipline)
        elif ":" in number:
            low, high = (part.strip() for part in number.split(":", 1))
            ranges.append(Q(department__code=discipline, code__gte=low, code__lte=high))
        else:
            full_codes.append(f"{discipline}-{number}")

    return any_of(
        ranges
        + [Q(full_code__in=full_codes)] * bool(full_codes)
        + [Q(department__code__in=departments)] * bool(departments)
        + [Q(code__in=codes)] * bool(codes)
    )


def evaluate_rop(rop, degree: Degree) -> bool | None:
    """
    One `<Rop>` relational operator evaluated against the degree being parsed. None when the
    left-hand side is something we cannot know, e.g. ALLDEGREES or NUMMAJORS.
    """
    left, operator, right = rop.get("Left"), rop.get("Operator"), rop.get("Right")

    match left:
        case "MAJOR":
            attribute = degree.major
        case "CONC" | "CONCENTRATION":
            attribute = degree.concentration or "NONE"
        case "PROGRAM":
            attribute = degree.program
        case "BANNERGPA":
            return operator in (">", ">=")  # assume a sufficiently high GPA
        case "ATTRIBUTE":
            return False  # assume the student does not have it
        case _:
            logger.warning(f"Unknowable left type in condition: {left}")
            return None

    match operator:
        case "=":
            return attribute == right
        case "<>":
            return attribute != right
        case _:
            raise LookupError(f"Unsupported relational operator in condition: {operator}")


def evaluate_condition(condition, degree: Degree) -> bool | None:
    """
    A `<LeftCondition>`/`<RightCondition>` subtree evaluated against the degree being parsed.
    """
    rop = condition.find("Rop")
    if rop is not None:
        return evaluate_rop(rop, degree)

    children = [child for child in condition if child.tag.endswith("Condition")]
    if not children:
        raise ValueError(f"Bad condition. Children: {[child.tag for child in condition]}")

    results = [evaluate_condition(child, degree) for child in children]
    if len(results) == 1:
        return results[0]
    if None in results:
        return None

    match condition.get("Connector"):
        case "AND":
            return all(results)
        case "OR":
            return any(results)
        case connector:
            raise LookupError(f"Unknown connector in condition: {connector}")


def audit_evaluation(rule_element) -> bool | None:
    match text_of(rule_element.find("BooleanEvaluation")):
        case "True":
            return True
        case "False":
            return False
        case "Unknown" | "":
            return None
        case value:
            raise LookupError(f"Unknown BooleanEvaluation: {value}")


def taken_branch(rule_element, degree: Degree):
    """
    The `<IfPart>` or `<ElsePart>` of an IfStmt, whichever the condition selects.

    Where our own evaluation disagrees with the audit's, ours wins: the audit is a what-if run
    against an empty record, so its BooleanEvaluation reflects a student with no GPA and no
    courses rather than the degree template. The audit's evaluation is the fallback for
    conditions we cannot evaluate at all.
    """
    requirement = rule_element.find("Requirement")
    evaluation = evaluate_condition(requirement.find("LeftCondition"), degree)
    from_audit = audit_evaluation(rule_element)

    if evaluation is None:
        evaluation = from_audit
    if evaluation is None:
        logger.warning(
            f"Evaluation unknown for rule {rule_element.get('Rule_id')}. Defaulting to False."
        )
        evaluation = False

    return requirement.find("IfPart" if evaluation else "ElsePart")


def own_share_targets(requirement) -> list[ShareTarget]:
    """The rule-scoped NONEXCLUSIVE qualifiers sitting directly on a `<Requirement>`."""
    return [
        target
        for qualifier in requirement.findall("Qualifier")
        if qualifier.get("Name") == "NONEXCLUSIVE"
        for target in parse_share_targets(qualifier)
    ]


def parse_share_targets(qualifier) -> list[ShareTarget]:
    """
    The targets of a NONEXCLUSIVE qualifier, read from its SubText: "(MAJOR)",
    "(OTHER = U-SEAS-WREE)" or "(MAJOR = AFRC, MAJOR = ANCH, ...)". Long lists are split
    across several SubText elements, so they are joined first.
    """
    targets = []
    for clause in subtext_of(qualifier).strip("()").split(","):
        kind, _, value = (part.strip() for part in clause.partition("="))
        if kind:
            targets.append(ShareTarget(kind, value or None))
    return targets


def make_rule(element, parent: Rule | None, **kwargs) -> Rule:
    return Rule(
        parent=parent,
        title=(element.get("Label") or "")[:MAX_TITLE_LENGTH],
        share_targets=own_share_targets(element.find("Requirement")),
        **kwargs,
    )


def parse_course_rule(element, parent: Rule | None) -> list[Rule]:
    """
    A Course rule states a number of classes required, a number of CUs required, or both.
    A rule requiring zero of either is not a rule.
    """
    requirement = element.find("Requirement")
    num = requirement.get("Classes_begin")
    credits = requirement.get("Credits_begin")
    if num is None and credits is None:
        raise ValueError("No Classes_begin or Credits_begin in Course requirement")

    num = int(num) if num is not None else None
    credits = float(credits) if credits is not None else None
    if num == 0 or credits == 0:
        return []

    rule = make_rule(element, parent, num=num, credits=credits)
    rule.q = repr(parse_requirement_courses(requirement))
    return [rule]


def parse_rule(element, degree: Degree, parent: Rule | None) -> list[Rule]:
    """The rules one `<Rule>` element contributes, parents before children, possibly none."""
    rule_type = element.get("RuleType")
    if rule_type in IGNORED_RULE_TYPES:
        return []

    match rule_type:
        case "Course":
            return parse_course_rule(element, parent)
        case "Subset":
            rule = make_rule(element, parent)
            return [rule, *parse_rules(element.findall("Rule"), degree, rule)]
        case "Group":
            rule = make_rule(element, parent)
            rule.num = int(element.find("Requirement").get("NumGroups"))
            return [rule, *parse_rules(element.findall("Rule"), degree, rule)]
        case "IfStmt":
            branch = taken_branch(element, degree)
            return parse_rules(branch.findall("Rule"), degree, parent) if branch else []
        case _:
            raise LookupError(f"Unknown rule type {rule_type}")


def parse_rules(elements, degree: Degree, parent: Rule | None = None) -> list[Rule]:
    """Mirrors `parse_degreeworks.parse_rulearray`."""
    return [rule for element in elements for rule in parse_rule(element, degree, parent)]


def parse_header_requirements(block, block_rule: Rule) -> list[Rule]:
    """
    A block's MINCLASS and MINCREDIT header qualifiers, as leaf rules.

    These constrain the courses already applied rather than competing for them: CSCI's
    "Area List - Networking" says that of the courses applied to the major, at least one must
    come from that list. A course counted elsewhere satisfies them at the same time, which in
    the Rule model is a share target.

    Which target depends on what the overlay ranges over. On a MAJOR or OTHER block it is
    THISBLOCK, since the courses it counts are the ones in that same block. On the DEGREE
    block it is ANYBLOCK: that block has no course rules of its own, so an overlay there --
    the College's "Arts and Sciences 31 CU Requirement", say -- ranges over the whole degree.

    Without this a CSCI degree would have no area list requirement at all.
    """
    scope = ANY_BLOCK if block.get("Req_type") == "DEGREE" else THIS_BLOCK
    requirements = []

    for qualifier in qualifiers(block, "MINCLASS", "MINCREDIT"):
        label, needed = qualifier.get("Label"), qualifier.get("Needed")
        if not label or not needed:
            # Unlabelled minimums are block-wide, already covered by the block's own credits.
            continue

        courses = parse_course_list(subtext_of(qualifier))
        if not courses:
            logger.warning(f"No courses parsed for qualifier {label!r}")
            continue

        is_classes = qualifier.get("Name") == "MINCLASS"
        requirements.append(
            Rule(
                parent=block_rule,
                title=label[:MAX_TITLE_LENGTH],
                q=repr(courses),
                num=int(needed) if is_classes else None,
                credits=None if is_classes else float(needed),
                share_targets=[ShareTarget(scope)],
            )
        )

    return requirements


def block_credits(block) -> Decimal | None:
    """
    A block's credit requirement. Blocks that impose none of their own -- the College's
    General Education blocks, for instance -- have no CLASSESCREDITS qualifier.
    """
    for qualifier in qualifiers(block, "CLASSESCREDITS"):
        if qualifier.get("Credits"):
            return Decimal(qualifier.get("Credits"))
    return None


def block_share_targets(block) -> list[ShareTarget]:
    """
    A block's own share policy.

    STANDALONEBLOCK counts as a target: it marks a block DegreeWorks evaluates outside the
    degree's shared pool of courses, so its courses also apply elsewhere without any ShareWith
    saying so. That is how the College's General Education Foundations block, a CS
    concentration and every minor work.
    """
    targets = []
    for qualifier in qualifiers(block, "NONEXCLUSIVE", "STANDALONEBLOCK"):
        if qualifier.get("Name") == "NONEXCLUSIVE":
            targets.extend(parse_share_targets(qualifier))
        else:
            targets.append(ShareTarget(ANY_BLOCK))
    return targets


def catalog_year_of(block) -> int | None:
    year = block.get("Cat_yr_start")
    return int(year) if year and year.isdigit() and int(year) > 0 else None


def apply_block_identity(rules: list[Rule], block_type: str, block_value: str, targets) -> None:
    """
    Denormalizes the block onto its rules, so a rule alone carries everything needed to decide
    what it may double count with.

    Rules arrive parents before children, so a rule's parent is already resolved and a
    qualifier on a Subset or Group reaches everything underneath it. Targets are held as
    ShareTargets while inheriting, then serialized for the JSON field.
    """
    for rule in rules:
        inherited = rule.parent.share_targets if rule.parent is not None else targets
        rule.block_type = block_type
        rule.block_value = block_value
        rule.share_targets = unique([*inherited, *rule.share_targets])

    for rule in rules:
        rule.share_targets = [target.as_dict() for target in rule.share_targets]


def parse_block(block, degree: Degree) -> tuple[ParsedBlock, list[Rule]]:
    """
    One `<Block>` as a ParsedBlock and its rules.

    A block whose rules all dissolve keeps no root rule -- a DEGREE block is usually just
    pointers to the other blocks -- but is still returned, since it carries the credit
    requirement and the block-level share policy.
    """
    block_type = block.get("Req_type")
    block_value = block.get("Req_value") or ""
    targets = block_share_targets(block)

    root = Rule(title=(block.get("Title") or "")[:MAX_TITLE_LENGTH], share_targets=[])
    rules = [
        root,
        *parse_rules(block.findall("Rule"), degree, root),
        *parse_header_requirements(block, root),
    ]
    apply_block_identity(rules, block_type, block_value, targets)

    if len(rules) == 1:
        rules, root = [], None

    return (
        ParsedBlock(
            req_type=block_type,
            req_value=block_value,
            title=block.get("Title") or "",
            credits=block_credits(block),
            catalog_year=catalog_year_of(block),
            root_rule=root,
            share_targets=targets,
        ),
        rules,
    )


def parse_audit(audit_xml: str, degree: Degree) -> ParsedAudit | None:
    """
    A Path@Penn audit as Rules, the degree's credit requirement and its share policy, or None
    if the audit states nothing a course can fulfill.

    A missing degree credit total is not a rejection. Second majors -- the "College 2nd Major
    ONLY" programs, CSCI-BA among them -- have a DEGREE block with no CLASSESCREDITS, because
    the total comes from the student's primary degree, and dropping them would lose exactly
    the programs a dual-major student needs.

    Note that this creates Rule objects but does not save them.
    """
    parsed = [
        parse_block(block, degree)
        for block in ET.fromstring(audit_xml).iter("Block")
        if block.get("Req_type") in BLOCK_TYPES
    ]
    blocks = [block for block, _ in parsed]
    rules = [rule for _, block_rules in parsed for rule in block_rules]

    if not any(rule.q for rule in rules):
        logger.error("Skipped audit because it has no rules a course can fulfill.")
        return None

    degree_block = next((block for block in blocks if block.req_type == "DEGREE"), None)
    years = {block.catalog_year for block in blocks if block.catalog_year}

    return ParsedAudit(
        degree_credits=degree_block.credits if degree_block else None,
        catalog_year=max(years, default=None),
        rules=rules,
        blocks=blocks,
    )


def save_rules(rules: list[Rule], owner) -> None:
    """
    Saves rules and attaches the top-level ones to `owner.rules`, which may be a Degree, a
    Major or a Minor. Rules are built parent-first, so saving in order gives every child a
    saved parent.
    """
    for rule in rules:
        assert (
            not rule.q or rule.num is not None or rule.credits is not None
        ), f"Rule {rule.title!r} has a query but no num or credits"
        rule.save()

    for rule in rules:
        if rule.parent is None:
            rule.refresh_from_db()
            owner.rules.add(rule)


def save_parsed_audit(parsed: ParsedAudit, degree: Degree) -> None:
    """
    Saves a degree and the rules parsed from its audit.

    The caller sets `degree.year` from `parsed.catalog_year` first, since the year is part of
    the Degree's unique constraint and so has to be known before the rows this replaces can be
    deleted. Mirrors `parse_degreeworks.parse_and_save_degreeworks`.
    """
    degree.credits = parsed.degree_credits
    degree.save()
    save_rules(parsed.rules, degree)
