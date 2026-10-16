"""
Which requirement slots a plan still needs.

A slot is one unit of remaining work on a leaf: a course count, a credit remainder, or both.
Ids are `slot:{rule_id}:{index}` and depend only on that leaf's remaining need, so an
unrelated fulfillment does not rename them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

from degree.models import TRANSFER_CREDIT_SEMESTER
from degree.utils.degree_logic import DEFAULT_COURSE_CREDITS, map_rules_and_degrees, prewarm_credits_cache


@dataclass
class OpenSlot:
    slot_id: str
    rule_id: int
    label: str
    cu: Decimal
    kind: str  # "listed" or "restriction"
    rule: object

    def as_dict(self):
        return {
            "slot_id": self.slot_id,
            "rule_id": self.rule_id,
            "label": self.label,
            "cu": float(self.cu),
            "kind": self.kind,
        }


def _ceil(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def _is_course_clause(node) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("type") == "COURSE":
        return True
    if node.get("type") == "OR":
        return bool(node.get("clauses")) and all(_is_course_clause(c) for c in node["clauses"])
    return False


def listed_course_codes(rule) -> list[str] | None:
    """
    Every course a leaf names, when the leaf is only a course list.

    A department, attribute, or level restriction returns none.
    """
    try:
        parsed = rule.q_json
    except Exception:
        return None
    codes = []

    def walk(node) -> bool:
        if not isinstance(node, dict):
            return False
        kind = node.get("type")
        if kind == "COURSE" and node.get("full_code"):
            codes.append(node["full_code"])
            return True
        if kind == "LEAF" and node.get("key") == "full_code" and node.get("value"):
            codes.append(node["value"])
            return True
        if kind == "LEAF" and node.get("key") == "full_code__in" and isinstance(node.get("value"), list):
            if not node["value"]:
                return False
            codes.extend(node["value"])
            return True
        if kind == "OR":
            clauses = node.get("clauses") or []
            return bool(clauses) and all(walk(clause) for clause in clauses)
        return False

    if not walk(parsed):
        return None
    unique = []
    for code in codes:
        if code not in unique:
            unique.append(code)
    return unique


# A requirements row can show this many courses. Past it, the row is a search.
SHORT_LIST_MAX = 8


def filter_panel_options(rule):
    """
    Courses that match a restriction, for the requirements panel.

    An explicit course list is decided from ``q_json`` on the client, so those
    rules return none. A department, attribute, or level restriction returns
    ``{"count": n}``. When ``n`` is at most ``SHORT_LIST_MAX``, ``courses`` is
    the codes to show as chips.
    """
    if listed_course_codes(rule) is not None:
        return None
    try:
        query = rule.get_q_object()
    except Exception:
        return {"count": 0, "courses": []}
    if not query:
        return {"count": 0, "courses": []}
    from courses.models import Course

    rows = (
        Course.objects.filter(query)
        .exclude(credits=None)
        .order_by("full_code")
        .distinct("full_code")
    )
    codes = list(rows.values_list("full_code", flat=True)[: SHORT_LIST_MAX + 1])
    if len(codes) <= SHORT_LIST_MAX:
        return {"count": len(codes), "courses": codes}
    return {"count": rows.count()}


def sole_listed_code(rule) -> str | None:
    """The one course a leaf names. A longer list stays a requirement stub."""
    codes = listed_course_codes(rule)
    if codes and len(codes) == 1:
        return codes[0]
    return None


def slot_kind(rule) -> str:
    """A leaf that is only a list of course codes is `listed`. Everything else is a restriction."""
    try:
        parsed = rule.q_json
    except Exception:
        parsed = None
    if parsed and _is_course_clause(parsed):
        return "listed"
    return "restriction"


def _describe(node, depth=0) -> str:
    if not isinstance(node, dict) or depth > 4:
        return "Elective"
    kind = node.get("type")
    if kind == "COURSE":
        return node.get("full_code") or "Course"
    if kind == "LEAF":
        key = node.get("key") or ""
        value = node.get("value")
        if key == "department__code":
            return f"{value} course"
        if key == "attributes__code__in" and isinstance(value, list):
            return "attribute " + ", ".join(str(v) for v in value[:3])
        if "code__" in key:
            return f"level {value}"
        return "Elective"
    clauses = node.get("clauses") or []
    parts = [_describe(c, depth + 1) for c in clauses[:4]]
    joiner = " or " if kind == "OR" else " and "
    text = joiner.join(p for p in parts if p)
    return text or "Elective"


def slot_label(rule) -> str:
    if rule.title:
        return rule.title
    try:
        parsed = rule.q_json
    except Exception:
        parsed = None
    if not parsed:
        return "Elective"
    return _describe(parsed)


def _unique(values):
    seen = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def _collect_schedule_parts(node, parts, negated=False):
    """Walk a parsed rule Q and keep the pieces a short schedule code is built from."""
    if not isinstance(node, dict):
        return
    kind = node.get("type")
    if kind == "NOT":
        for child in node.get("clauses") or []:
            _collect_schedule_parts(child, parts, negated=True)
        return
    if negated:
        return
    if kind == "COURSE":
        if node.get("full_code"):
            parts["courses"].append(node["full_code"])
        return
    if kind == "LEAF":
        key = node.get("key") or ""
        value = node.get("value")
        if key == "department__code" and value:
            parts["depts"].append(value)
        elif key == "department__code__in" and isinstance(value, list):
            parts["depts"].extend(value)
        elif key == "attributes__code__in" and isinstance(value, list):
            parts["attrs"].extend(value)
        elif key == "full_code__in" and isinstance(value, list):
            parts["courses"].extend(value)
        elif key == "full_code__startswith" and value:
            parts["depts"].append(str(value).rstrip("-"))
        elif key == "code__gte":
            parts["gte"] = value
        elif key == "code__lte":
            parts["lte"] = value
        return
    for child in node.get("clauses") or []:
        _collect_schedule_parts(child, parts)


def _level_code(gte, lte):
    def as_number(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    upper = as_number(lte)
    if upper is not None and upper >= 9000:
        upper = None
    if gte is not None and upper is not None:
        return f"{gte}–{upper}"
    if gte is not None:
        return f"{gte}+"
    if upper is not None:
        return f"≤{upper}"
    return ""


def _ancestor_titles(rule) -> str:
    titles = []
    current = rule
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        title = (getattr(current, "title", None) or "").strip()
        if title:
            titles.append(title)
        current = getattr(current, "parent", None)
    return " ".join(titles)


def is_writing_rule(rule) -> bool:
    """A writing seminar is a course of its own, even inside a general-education block."""
    if "writ" in (getattr(rule, "title", None) or "").lower():
        return True
    # A college CU overlay lists WRIT among many departments. That is not writing.
    return rule_departments(rule) == {"WRIT"}


def is_coverage_rule(rule) -> bool:
    """
    A general-education label carried by courses already in the degree.

    Sectors and foundational approaches are not extra courses. Writing stays a
    real course, and so does anything outside a general-education block.
    """
    if is_writing_rule(rule):
        return False
    titles = _ancestor_titles(rule).lower()
    return (
        "general education" in titles
        or "foundational approach" in titles
        or "sector" in titles
    )


def is_free_elective_floor(rule) -> bool:
    """
    A credit minimum over the college's own departments, such as the Arts and
    Sciences 30 CU requirement.

    It is not a list of courses to schedule. Courses already in the degree
    count toward it, and the credits still missing are free electives.
    """
    if getattr(rule, "credits", None) is None:
        return False
    return "cu requirement" in _ancestor_titles(rule).lower()


def rule_departments(rule) -> set[str]:
    """Department codes a leaf names. Empty when the leaf is not a department rule."""
    parts = {"courses": [], "depts": [], "attrs": [], "gte": None, "lte": None}
    try:
        parsed = rule.q_json
    except Exception:
        parsed = None
    if parsed:
        _collect_schedule_parts(parsed, parts)
    return {str(code).upper() for code in parts["depts"]}


def schedule_exception(rule) -> str | None:
    """
    Named schedule stubs that should not be collapsed into a course list.

    Business breadth is every Wharton department, so the card says
    `WH Business Breadth` instead of `ACCT/BEPP/FNCE/...`. A college CU
    requirement is a free elective, not the department list inside it.
    """
    if is_free_elective_floor(rule):
        return "Free Elective"
    titles = _ancestor_titles(rule).lower()
    if "business breadth" in titles:
        return "WH Business Breadth"
    return None


def _course_list_code(codes):
    unique = _unique(codes)
    shown = [code.replace("-", " ") for code in unique]
    if not shown:
        return ""
    if len(shown) == 1:
        return shown[0]
    departments = []
    for code in unique:
        department = code.split("-")[0] if "-" in code else ""
        if department and department not in departments:
            departments.append(department)
    # A long list from one department is that department. The option count
    # on the card opens the courses.
    if len(shown) > 2 and len(departments) == 1:
        return departments[0]
    if len(shown) == 2:
        return f"{shown[0]}/{shown[1]}"
    return f"{shown[0]}/{shown[1]} (+{len(shown) - 2})"


def schedule_code(rule) -> str:
    """
    Short label for a schedule card.

    A list of courses becomes `CIS 1100/CIS 1200 (+3)`. A department, attribute,
    or level restriction becomes `ESE 2000+` or `MATH/PHYS`. Named exceptions
    such as business breadth keep their own stub. The full rule title stays on
    the requirements panel.
    """
    exception = schedule_exception(rule)
    if exception:
        return exception
    try:
        parsed = rule.q_json
    except Exception:
        parsed = None
    parts = {"courses": [], "depts": [], "attrs": [], "gte": None, "lte": None}
    if parsed:
        _collect_schedule_parts(parsed, parts)
    depts = "/".join(_unique(parts["depts"]))
    attrs = "/".join(_unique(parts["attrs"]))
    level = _level_code(parts["gte"], parts["lte"])
    if depts or attrs or level:
        return " ".join(piece for piece in (depts, attrs, level) if piece)
    listed = _course_list_code(parts["courses"])
    if listed:
        return listed
    title = (getattr(rule, "title", None) or "").strip()
    if not title:
        return "Elective"
    if len(title) <= 18:
        return title
    return title[:18].rstrip() + "…"


def slot_cus(num_remaining, credits_remaining) -> list[Decimal]:
    """
    How many slots a leaf still needs, and the CU of each.

    A leaf with both a course count and a credit minimum emits enough slots for whichever
    remainder is larger. Every slot is 1 CU except a trailing fraction when credits do not
    land on a whole number.
    """
    count = 0
    if num_remaining:
        count = int(num_remaining)
    if credits_remaining is not None and credits_remaining > 0:
        count = max(count, _ceil(credits_remaining))
    if count <= 0:
        return []
    cus = [Decimal("1")] * count
    if credits_remaining is not None and credits_remaining > 0:
        whole = int(credits_remaining)
        frac = credits_remaining - Decimal(whole)
        if frac > 0:
            cus[-1] = frac
    return cus


def _progress_for(fulfillments, credits_cache):
    progress = {}

    def add(rule, cu):
        bucket = progress.setdefault(rule.id, {"count": 0, "cu": Decimal(0)})
        bucket["count"] += 1
        bucket["cu"] += cu

    for fulfillment in fulfillments:
        cu = credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)
        claimed = set(fulfillment.rules.all()) | set(fulfillment.overrides.all())
        for rule in claimed:
            add(rule, cu)
    return progress


def _remaining(rule, progress):
    bucket = progress.get(rule.id, {"count": 0, "cu": Decimal(0)})
    num_remaining = None
    credits_remaining = None
    if rule.num is not None:
        num_remaining = max(0, rule.num - bucket["count"])
    if rule.credits is not None:
        credits_remaining = max(Decimal(0), Decimal(rule.credits) - bucket["cu"])
    return num_remaining, credits_remaining


def _leaf_done(rule, progress) -> bool:
    num_remaining, credits_remaining = _remaining(rule, progress)
    if num_remaining is None and credits_remaining is None:
        return True
    num_ok = num_remaining is None or num_remaining == 0
    credits_ok = credits_remaining is None or credits_remaining <= 0
    return num_ok and credits_ok


def _score(rule, progress) -> float:
    """0 to 1, how far this rule (or its subtree) already is. Used to commit an N-of-M branch."""
    if rule.q:
        parts = []
        bucket = progress.get(rule.id, {"count": 0, "cu": Decimal(0)})
        if rule.num:
            parts.append(min(1.0, bucket["count"] / rule.num))
        if rule.credits:
            parts.append(min(1.0, float(bucket["cu"] / Decimal(rule.credits))))
        return sum(parts) / len(parts) if parts else 1.0
    children = list(rule.children.all())
    if not children:
        return 1.0
    return sum(_score(child, progress) for child in children) / len(children)


def _committed(rule, progress):
    children = sorted(rule.children.all(), key=lambda child: child.id)
    if rule.num is None:
        return children
    ranked = sorted(children, key=lambda child: (-_score(child, progress), child.id))
    return ranked[: rule.num]


def _emit(rule, progress, slots, keep_ids):
    if rule.q:
        if rule.id not in keep_ids or _leaf_done(rule, progress):
            return
        num_remaining, credits_remaining = _remaining(rule, progress)
        kind = slot_kind(rule)
        label = slot_label(rule)
        for index, cu in enumerate(slot_cus(num_remaining, credits_remaining)):
            slots.append(
                OpenSlot(
                    slot_id=f"slot:{rule.id}:{index}",
                    rule_id=rule.id,
                    label=label,
                    cu=cu,
                    kind=kind,
                    rule=rule,
                )
            )
        return
    for child in _committed(rule, progress):
        _emit(child, progress, slots, keep_ids)


def open_slots(degree_plan) -> list[OpenSlot]:
    """Open slots in component order, then tree order. Fully satisfied plans return none."""
    plan_rules = map_rules_and_degrees(degree_plan)
    fulfillments = list(
        degree_plan.fulfillments.prefetch_related("rules", "overrides").order_by("full_code")
    )
    credits_cache = prewarm_credits_cache([f.full_code for f in fulfillments])
    progress = _progress_for(fulfillments, credits_cache)

    slots: list[OpenSlot] = []
    for component in plan_rules.composition.components:
        roots = list(component.roots) or [
            rule for rule in component.rules if rule.parent_id is None
        ]
        for root in sorted(roots, key=lambda rule: rule.id):
            _emit(root, progress, slots, component.keep_ids)
    return slots


def unplaced_fulfillments(degree_plan):
    """Courses the student owns that are not yet in a semester. Transfer credit stays put."""
    return [
        fulfillment
        for fulfillment in degree_plan.fulfillments.all()
        if not fulfillment.semester and fulfillment.semester != TRANSFER_CREDIT_SEMESTER
    ]
