"""
Tools that read and modify the student's own Penn Course Plan data.

Everything here is scoped to `request.user`. The model never supplies an identity —
no tool schema in this module accepts one — so it can only ever reach the schedules
of the student it is talking to.

A note on writes. Penn Course Plan's frontend keeps its own copy of the schedule and
syncs on a timer: it pulls every 5 seconds, and pushes only when it has local edits
that have not reached the server (`frontend/plan/components/syncutils.js`). So a
change made here shows up in an open PCP tab within a few seconds. It is only at risk
of being overwritten if the student is editing that tab in the same moment, which is
why these tools stay additive and never delete a schedule.
"""

from itertools import combinations

from django.conf import settings
from django.db import transaction

from chat.errors import ToolError
from chat.formatting import meeting_spans, meeting_times, number
from courses.models import Section
from plan.models import Schedule


# Penn Course Plan stores the cart as a schedule with this name.
CART_NAME = "cart"

# Mirrors PCP's own schedule API, which refuses writes to this schedule because it
# reflects what the student actually registered for on Path@Penn.
RESERVED_NAMES = {settings.PATH_REGISTRATION_SCHEDULE_NAME}

# A single tool call should not be able to rewrite a whole schedule at once.
MAX_SECTIONS_PER_WRITE = 10


def _schedule_label(schedule):
    return "cart" if schedule.name == CART_NAME else schedule.name


def _section_row(section):
    return {
        "section_id": section.full_code,
        "course_code": section.course.full_code,
        "title": section.course.title,
        "activity": section.get_activity_display(),
        "credits": number(section.credits),
        "instructors": [i.name for i in section.instructors.all()],
        "meeting_times": meeting_times(section.meetings.all()),
    }


def _find_conflicts(entries):
    """
    Pairwise time overlaps among `(label, spans)` entries.

    Sections with no meetings — async courses, TBA rooms — have no spans and so never
    conflict, which is the right answer rather than an omission.
    """
    conflicts = []
    for (label_a, spans_a), (label_b, spans_b) in combinations(entries, 2):
        for day_a, start_a, end_a in spans_a:
            clash = any(
                day_b == day_a and start_a < end_b and start_b < end_a
                for day_b, start_b, end_b in spans_b
            )
            if clash:
                conflicts.append({"between": [label_a, label_b], "day": day_a})
                break
    return conflicts


def _summarize(schedule):
    sections = list(schedule.sections.all())
    breaks = [b for b in schedule.breaks.all() if b.checked]

    entries = [(s.full_code, meeting_spans(s.meetings.all())) for s in sections]
    entries += [(b.name, meeting_spans(b.meetings.all())) for b in breaks]

    credits = [s.credits for s in sections if s.credits is not None]

    # A section with no meetings can never overlap anything, so an empty `conflicts`
    # would otherwise read as "this schedule is clear" when the truth is "we have no
    # times to check". Some sections are genuinely untimed (async, TBA), and a
    # semester whose meeting data has not been imported yet looks the same from here.
    untimed = [s.full_code for s in sections if not s.meetings.all()]

    return {
        "name": _schedule_label(schedule),
        "is_cart": schedule.name == CART_NAME,
        "is_primary": schedule.is_primary,
        "semester": schedule.semester,
        "total_credits": number(sum(credits)) if credits else 0,
        "sections": [_section_row(s) for s in sections],
        "breaks": [
            {"name": b.name, "meeting_times": meeting_times(b.meetings.all())} for b in breaks
        ],
        "conflicts": _find_conflicts(entries),
        "sections_without_meeting_times": untimed,
        "conflicts_fully_checked": not untimed,
    }


def _schedules_queryset(user, semester):
    return (
        Schedule.objects.filter(person=user, semester=semester)
        .prefetch_related(
            "sections__course",
            "sections__instructors",
            "sections__meetings",
            "breaks__meetings",
            "primary_schedule",
        )
        .order_by("name")
    )


def _writable(user, semester, schedule_name):
    """Resolve a schedule name to write to, creating it if the student has none."""
    name = (schedule_name or CART_NAME).strip() or CART_NAME
    if name.lower() == CART_NAME:
        name = CART_NAME

    if name in RESERVED_NAMES:
        raise ToolError(
            f"'{name}' mirrors what the student registered for on Path@Penn and cannot "
            "be edited here. Use the cart or one of their own schedules."
        )

    schedule, created = Schedule.objects.get_or_create(person=user, semester=semester, name=name)
    return schedule, created


def _resolve_sections(section_ids, semester):
    if not section_ids:
        raise ToolError("No sections given.")
    if len(section_ids) > MAX_SECTIONS_PER_WRITE:
        raise ToolError(
            f"At most {MAX_SECTIONS_PER_WRITE} sections at a time; "
            f"{len(section_ids)} were given."
        )

    wanted = [str(code).strip().upper() for code in section_ids]
    sections = list(
        Section.objects.filter(full_code__in=wanted, course__semester=semester)
        .select_related("course")
        .prefetch_related("instructors", "meetings")
    )

    missing = set(wanted) - {s.full_code for s in sections}
    if missing:
        raise ToolError(
            f"No section in {semester} matches {', '.join(sorted(missing))}. Section "
            "codes look like CIS-1200-001 — call get_course to see which sections a "
            "course actually has this semester."
        )
    return sections


def get_my_schedules(*, user, semester):
    """Every schedule the student has for the semester, including their cart."""
    schedules = [_summarize(s) for s in _schedules_queryset(user, semester)]
    return {
        "semester": semester,
        "schedules": schedules,
        "note": (
            "The student has no schedules or cart for this semester yet." if not schedules else None
        ),
    }


def add_to_schedule(
    *,
    user,
    semester,
    section_ids,
    schedule_name=None,
    allow_missing_meeting_times=False,
):
    """Add sections to the cart or a named schedule, creating the schedule if needed."""
    sections = _resolve_sections(section_ids, semester)

    # A section with no published meeting times cannot be checked against anything for
    # conflicts, and Penn Course Plan draws its calendar from meetings, so it will not
    # appear there either. Adding one silently leaves a student with a schedule that
    # looks emptier than it is, so this takes a deliberate second call.
    untimed = [s.full_code for s in sections if not s.meetings.all()]
    if untimed and not allow_missing_meeting_times:
        raise ToolError(
            f"{', '.join(sorted(untimed))} has no published meeting times, so it cannot "
            "be checked for conflicts and will not show on the student's Penn Course "
            "Plan calendar. Tell them that and ask whether to add it anyway; if they "
            "say yes, call this again with allow_missing_meeting_times set to true."
        )

    with transaction.atomic():
        schedule, created = _writable(user, semester, schedule_name)
        present = set(schedule.sections.values_list("full_code", flat=True))
        added = [s for s in sections if s.full_code not in present]
        if added:
            schedule.sections.add(*added)
            # Touch `updated_at` so an open PCP tab treats this as the newer copy.
            schedule.save()

    # Read the schedule back and confirm the write actually landed, rather than
    # reporting what we asked for. Everything downstream — what the assistant tells the
    # student, what they believe is in their cart — rests on this being true and not
    # merely attempted.
    schedule = _schedules_queryset(user, semester).get(pk=schedule.pk)
    summary = _summarize(schedule)
    in_schedule = {row["section_id"] for row in summary["sections"]}

    requested = [s.full_code for s in sections]
    confirmed = [code for code in requested if code in in_schedule]
    failed = [code for code in requested if code not in in_schedule]

    return {
        "added": [s.full_code for s in added if s.full_code in in_schedule],
        "added_without_meeting_times": [
            s for s in untimed if s in {a.full_code for a in added} and s in in_schedule
        ],
        "already_present": [s.full_code for s in sections if s.full_code in present],
        "created_schedule": created,
        # Read back from the database after the write, not assumed from the request.
        "confirmed_in_schedule": confirmed,
        "failed_to_add": failed,
        "schedule": summary,
    }


def remove_from_schedule(*, user, semester, section_ids, schedule_name=None):
    """Remove sections from the cart or a named schedule."""
    name = (schedule_name or CART_NAME).strip() or CART_NAME
    if name.lower() == CART_NAME:
        name = CART_NAME
    if name in RESERVED_NAMES:
        raise ToolError(
            f"'{name}' mirrors what the student registered for on Path@Penn and cannot "
            "be edited here."
        )

    schedule = Schedule.objects.filter(person=user, semester=semester, name=name).first()
    if schedule is None:
        raise ToolError(
            f"The student has no schedule named '{name}' for {semester}. Call "
            "get_my_schedules to see what they have."
        )

    wanted = {str(code).strip().upper() for code in section_ids or []}
    if not wanted:
        raise ToolError("No sections given.")

    with transaction.atomic():
        present = list(schedule.sections.filter(full_code__in=wanted))
        if present:
            schedule.sections.remove(*present)
            schedule.save()

    removed = {s.full_code for s in present}
    schedule = _schedules_queryset(user, semester).get(pk=schedule.pk)
    summary = _summarize(schedule)
    in_schedule = {row["section_id"] for row in summary["sections"]}

    # Same read-back as adding: confirm they are gone rather than assuming.
    return {
        "removed": sorted(code for code in removed if code not in in_schedule),
        "failed_to_remove": sorted(code for code in removed if code in in_schedule),
        "not_in_schedule": sorted(wanted - removed),
        "schedule": summary,
    }


PLAN_TOOL_IMPLEMENTATIONS = {
    "get_my_schedules": get_my_schedules,
    "add_to_schedule": add_to_schedule,
    "remove_from_schedule": remove_from_schedule,
}


SCHEDULE_NAME_PARAM = {
    "type": "string",
    "description": (
        "Which schedule to use. Omit or pass 'cart' for the student's cart, which is "
        "where courses go when they are still deciding. Otherwise the name of one of "
        "their schedules, exactly as get_my_schedules reports it."
    ),
}

SECTION_IDS_PARAM = {
    "type": "array",
    "items": {"type": "string"},
    "description": (
        "Full section codes, e.g. ['CIS-1200-001', 'CIS-1200-201']. A section code is "
        "a course code plus a section number — not a course code on its own. Many "
        "courses need both a lecture and a recitation or lab; call get_course first "
        "to see what sections exist and include each part the student needs."
    ),
}


PLAN_TOOLS = [
    {
        "name": "get_my_schedules",
        "description": (
            "The student's own Penn Course Plan schedules for the semester, including "
            "their cart: every section with its meeting times and instructors, their "
            "breaks, total course units, and any time conflicts. Call this before "
            "answering anything about what they are taking, whether something fits, or "
            "how full their schedule is."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "semester": {
                    "type": "string",
                    "description": (
                        "Semester as YYYYx. Defaults to the student's current planning " "semester."
                    ),
                },
            },
        },
    },
    {
        "name": "add_to_schedule",
        "description": (
            "Add sections to the student's cart or one of their schedules. Creates the "
            "schedule if they do not have one by that name. Adding is idempotent — a "
            "section already there is reported back rather than duplicated. Returns the "
            "updated schedule, including any time conflicts the addition causes, which "
            "you should tell the student about. The schedule is read back from the "
            "database afterwards: `confirmed_in_schedule` lists what is verifiably "
            "there now, and `failed_to_add` lists anything that did not land. Report "
            "only what those confirm."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section_ids": SECTION_IDS_PARAM,
                "schedule_name": SCHEDULE_NAME_PARAM,
                "semester": {"type": "string", "description": "Semester as YYYYx."},
                "allow_missing_meeting_times": {
                    "type": "boolean",
                    "description": (
                        "Add a section even though it has no published meeting times. "
                        "Leave this off. Adding such a section is refused by default, "
                        "because it cannot be checked for conflicts and will not appear "
                        "on the student's calendar; set it only after you have told the "
                        "student that and they have said to add it anyway."
                    ),
                },
            },
            "required": ["section_ids"],
        },
    },
    {
        "name": "remove_from_schedule",
        "description": (
            "Remove sections from the student's cart or one of their schedules. Only "
            "use this when the student has asked for something to be taken out. The "
            "schedule is read back afterwards: `removed` lists what is verifiably gone "
            "and `failed_to_remove` anything still there."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section_ids": SECTION_IDS_PARAM,
                "schedule_name": SCHEDULE_NAME_PARAM,
                "semester": {"type": "string", "description": "Semester as YYYYx."},
            },
            "required": ["section_ids"],
        },
    },
]
