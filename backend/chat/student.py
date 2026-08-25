"""
What the student has already taken or planned, in a form the catalog tools can check
against.

The wrinkle is crosslisting. Penn lists one course under several codes — most often an
undergraduate and a graduate number for the same class, like CIS-4480 and CIS-5480 —
and PCX models that with `Course.primary_listing`. A student who took CIS-4480 has
taken CIS-5480; recommending the other number would be recommending the same course
back to them. So every code here is expanded to its whole crosslisting group before
anything is compared.
"""

from collections import defaultdict

from courses.models import Course
from degree.models import Fulfillment
from plan.models import Schedule


def crosslistings_for(codes):
    """
    Map each of `codes` to the other codes the same course is listed under.

    A course code appears once per semester it was offered, and crosslistings can
    change between semesters, so this unions the groups across every offering.
    """
    codes = {c for c in codes if c}
    if not codes:
        return {}

    primaries = set(
        Course.objects.filter(full_code__in=codes).values_list("primary_listing_id", flat=True)
    )
    if not primaries:
        return {code: set() for code in codes}

    by_primary = defaultdict(set)
    for primary_id, full_code in Course.objects.filter(
        primary_listing_id__in=primaries
    ).values_list("primary_listing_id", "full_code"):
        by_primary[primary_id].add(full_code)

    # Which groups a code belongs to, unioned.
    groups = defaultdict(set)
    for full_code, primary_id in Course.objects.filter(full_code__in=codes).values_list(
        "full_code", "primary_listing_id"
    ):
        groups[full_code] |= by_primary[primary_id]

    return {code: groups.get(code, set()) - {code} for code in codes}


def _expand(codes):
    """`codes` plus every other code those courses are listed under."""
    codes = set(codes)
    for code, others in crosslistings_for(codes).items():
        codes |= others
    return codes


def course_history(user, semester):
    """
    The student's completed and planned courses, expanded across crosslistings.

    "Completed" comes from degree-plan fulfillments dated before the current semester —
    the only record of what a student has actually taken. "Planned" is everything else
    they have lined up: later fulfillments, and whatever is in their cart or schedules.

    Returns `{"completed": set, "planned": set}`. A course counts as completed rather
    than planned when it is in both.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return {"completed": set(), "planned": set()}

    completed = set()
    planned = set()

    for full_code, sem in Fulfillment.objects.filter(degree_plan__person=user).values_list(
        "full_code", "semester"
    ):
        if sem and sem < semester:
            completed.add(full_code)
        else:
            planned.add(full_code)

    planned |= set(
        Schedule.objects.filter(person=user, semester=semester).values_list(
            "sections__course__full_code", flat=True
        )
    )
    planned.discard(None)

    completed = _expand(completed)
    planned = _expand(planned) - completed
    return {"completed": completed, "planned": planned}
