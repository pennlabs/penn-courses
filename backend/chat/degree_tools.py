"""
Tools that read the student's Penn Degree Plan.

A degree's requirements are a tree of `Rule`s: a leaf carries a `q` query describing
which courses count and how many are needed, and a branch requires some number of its
children. The student's progress is a set of `Fulfillment`s — a course, a semester,
and the rules it was counted toward.

Handing that tree to a model verbatim does not work. A single degree can carry dozens
of rules, and the parts a student is asking about are almost always the unfinished
ones. So a satisfied branch collapses to a single line and its children are dropped,
while anything outstanding is expanded down to the leaf, with the rule's id attached
so `search_courses` can be pointed straight at it.
"""

from decimal import Decimal

from chat.errors import ToolError
from chat.formatting import number
from chat.student import crosslistings_for
from courses.models import Course
from degree.models import DegreePlan, Rule


# A whole degree's rule tree can be enormous. Unsatisfied requirements are what a
# student asks about, so they are what the budget is spent on.
MAX_NODES = 150


def _course_credits(full_codes):
    """Credits per course code, taken from the most recent offering of each."""
    credits = {}
    rows = (
        Course.objects.filter(full_code__in=full_codes, credits__isnull=False)
        .order_by("full_code", "-semester")
        .values_list("full_code", "credits", "title")
    )
    for full_code, value, title in rows:
        credits.setdefault(full_code, (value, title))
    return credits


def _requirement(rule):
    """What a rule asks for, as a phrase the model can quote."""
    parts = []
    if rule.num is not None:
        noun = "course" if rule.q else "requirement"
        parts.append(f"{rule.num} {noun}{'s' if rule.num != 1 else ''}")
    if rule.credits is not None:
        parts.append(f"{number(rule.credits)} CU")
    return " and ".join(parts) or "all of the below"


def _build(rule, by_rule, catalog, budget):
    """
    Turn one rule into a node, depth first, so a branch knows whether its children are
    done before deciding how much of itself to show.
    """
    children = [_build(child, by_rule, catalog, budget) for child in rule.children.all()]

    if rule.q:
        assigned = by_rule.get(rule.id, [])
        courses = len(assigned)
        earned = sum(
            (catalog.get(f.full_code, (Decimal(0), None))[0] or Decimal(0)) for f in assigned
        )
        satisfied = (rule.num is None or courses >= rule.num) and (
            rule.credits is None or earned >= rule.credits
        )
        progress = {"courses": courses, "credits": number(earned)}
    else:
        done = sum(1 for child in children if child["satisfied"])
        satisfied = done >= (rule.num if rule.num is not None else len(children))
        assigned = []
        progress = {"requirements_met": done, "of": len(children)}

    node = {
        "rule_id": rule.id,
        "title": rule.title or "(untitled requirement)",
        "requires": _requirement(rule),
        "satisfied": satisfied,
        "progress": progress,
    }

    if assigned:
        node["counted_courses"] = [
            {"full_code": f.full_code, "semester": f.semester} for f in assigned
        ]

    # A finished branch is reported, not enumerated — the student is not asking about
    # requirements they have already met.
    if satisfied:
        return node

    if rule.q:
        # Only leaves can be searched against, and only unmet ones are worth searching.
        node["searchable_with"] = {"rule_ids": str(rule.id)}
    if children:
        budget["remaining"] -= len(children)
        if budget["remaining"] < 0:
            node["children_omitted"] = len(children)
        else:
            node["children"] = children
    return node


def _degree_row(degree):
    return {
        "program": degree.program,
        "degree": degree.degree,
        "major": degree.major_name or degree.major,
        "concentration": degree.concentration_name or degree.concentration,
        "catalog_year": degree.year,
        "credits_required": number(degree.credits),
    }


def _summarize_plan(plan, current_semester):
    fulfillments = list(plan.fulfillments.prefetch_related("rules"))
    catalog = _course_credits([f.full_code for f in fulfillments])

    by_rule = {}
    for fulfillment in fulfillments:
        for rule in fulfillment.rules.all():
            by_rule.setdefault(rule.id, []).append(fulfillment)

    rules = (
        Rule.objects.filter(degrees__in=plan.degrees.all(), parent__isnull=True)
        .distinct()
        .prefetch_related("children__children__children")
    )
    budget = {"remaining": MAX_NODES}
    requirements = [_build(rule, by_rule, catalog, budget) for rule in rules]

    # A student who took CIS-4480 has taken CIS-5480 — same class, two numbers.
    # Carrying the other codes here is what stops the graduate listing of something
    # they already did from being recommended back to them.
    crosslistings = crosslistings_for([f.full_code for f in fulfillments])

    def course_row(f):
        value, title = catalog.get(f.full_code, (None, None))
        row = {
            "full_code": f.full_code,
            "title": title,
            "semester": f.semester,
            "credits": number(value),
            "counts_toward": [r.title for r in f.rules.all() if r.title],
        }
        also = sorted(crosslistings.get(f.full_code) or ())
        if also:
            row["also_listed_as"] = also
        return row

    # Semesters are YYYYx with x ordered A < B < C, so they compare chronologically
    # as plain strings.
    taken = [f for f in fulfillments if f.semester and f.semester < current_semester]
    planned = [f for f in fulfillments if f.semester and f.semester >= current_semester]
    undated = [f for f in fulfillments if not f.semester]

    def total(items):
        return number(
            sum((catalog.get(f.full_code, (Decimal(0), None))[0] or Decimal(0)) for f in items)
        )

    return {
        "name": plan.name,
        "degrees": [_degree_row(d) for d in plan.degrees.all()],
        "credits_required": number(sum((d.credits or Decimal(0)) for d in plan.degrees.all())),
        "credits_completed": total(taken),
        "credits_planned": total(planned),
        "courses_completed": [course_row(f) for f in sorted(taken, key=lambda f: f.semester)],
        "courses_planned": [course_row(f) for f in sorted(planned, key=lambda f: f.semester)],
        "courses_without_a_semester": [course_row(f) for f in undated],
        "requirements": requirements,
        "note": (
            "Requirements marked satisfied are collapsed; their sub-requirements are "
            "not listed. Unsatisfied leaf requirements carry `searchable_with`, whose "
            "rule_ids can be passed to search_courses to find courses that count."
        ),
    }


def get_my_degree_plan(*, user, semester, plan_name=None):
    """The student's degree plan: what it requires, what they have done, what is left."""
    plans = DegreePlan.objects.filter(person=user).prefetch_related(
        "degrees", "fulfillments__rules"
    )
    if plan_name:
        plans = plans.filter(name=plan_name)

    plans = list(plans.order_by("-updated_at"))
    if not plans:
        if plan_name:
            raise ToolError(
                f"The student has no degree plan named '{plan_name}'. Call "
                "get_my_degree_plan without a name to see what they have."
            )
        return {
            "degree_plans": [],
            "note": (
                "The student has not built a degree plan in Penn Degree Plan yet, so "
                "there is nothing to check requirements against. They can create one "
                "at penndegreeplan.com."
            ),
        }

    # More than one plan usually means the student is comparing majors; the most
    # recently touched one is what they mean by "my plan".
    return {
        "degree_plans": [_summarize_plan(plan, semester) for plan in plans],
    }


DEGREE_TOOL_IMPLEMENTATIONS = {
    "get_my_degree_plan": get_my_degree_plan,
}


DEGREE_TOOLS = [
    {
        "name": "get_my_degree_plan",
        "description": (
            "The student's Penn Degree Plan: their degree and major, the courses they "
            "have completed and planned, and their requirements with what is still "
            "outstanding. Requirements they have already satisfied are summarized "
            "rather than listed in full. Each unsatisfied leaf requirement includes "
            "`searchable_with.rule_ids`, which you can pass to search_courses to find "
            "courses that would count toward it. Call this before advising on what a "
            "student still needs, or whether a course fills a gap."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_name": {
                    "type": "string",
                    "description": (
                        "Which degree plan, if the student has more than one. Omit for "
                        "all of them, most recently edited first."
                    ),
                },
            },
        },
    },
]
