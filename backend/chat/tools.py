"""
Read-only tools exposed to the chat assistant.

Each tool is a plain function taking keyword arguments matching its JSON schema in
`TOOLS`, plus a `semester` fallback, and returning a JSON-serializable value. Tool
results are fed straight back to the model, so they are projected down to the fields
a student would actually care about rather than serialized in full — the wire format
of the PCX REST API is tuned for the frontend, not for a context window.
"""

from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.http import QueryDict

from chat.degree_tools import DEGREE_TOOL_IMPLEMENTATIONS, DEGREE_TOOLS
from chat.errors import ToolError
from chat.formatting import meeting_times, number
from chat.plan_tools import PLAN_TOOL_IMPLEMENTATIONS, PLAN_TOOLS
from chat.student import course_history, crosslistings_for
from courses.filters import CourseSearchFilterBackend
from courses.models import Course, Section
from courses.search import TypedCourseSearchBackend


# Cap on rows pulled out of the DB before ranking. Ranking happens in Python because
# the search filter backend ends in `.distinct("full_code")`, and Postgres requires a
# DISTINCT ON query's ORDER BY to lead with the distinct column.
SEARCH_CANDIDATE_LIMIT = 200

# Default and maximum number of courses returned to the model from one search.
SEARCH_DEFAULT_LIMIT = 15
SEARCH_MAX_LIMIT = 40

# Course descriptions run long; the model rarely needs the whole thing to triage a
# search result. `get_course` returns the untruncated description.
SEARCH_DESCRIPTION_CHARS = 300

REVIEW_FIELDS = ("course_quality", "instructor_quality", "difficulty", "work_required")

REVIEW_CACHE_TTL = 60 * 60 * 24  # 1 day

# Blurbs shown next to a course code in the chat transcript; shorter than a search row.
PREVIEW_DESCRIPTION_CHARS = 220


def _review_bits(reviews):
    """
    Project one of PCR's rCamelCase score dicts down to the four headline fields.
    Returns None if none of them are present, so the model sees an explicit absence
    rather than a dict of nulls.
    """
    if not reviews:
        return None
    bits = {
        field: number(reviews.get("r" + "".join(p.title() for p in field.split("_"))))
        for field in REVIEW_FIELDS
    }
    if not any(v is not None for v in bits.values()):
        return None
    return bits


def _course_ratings(course):
    """The review annotations `Course.with_reviews` puts on each row."""
    bits = {field: number(getattr(course, field, None)) for field in REVIEW_FIELDS}
    if not any(v is not None for v in bits.values()):
        return None
    return bits


def _section_row(section):
    return {
        "section_id": section.full_code,
        "activity": section.get_activity_display(),
        "status": section.get_status_display(),
        "credits": number(section.credits),
        "instructors": [i.name for i in section.instructors.all()],
        "meeting_times": meeting_times(section.meetings.all()),
    }


class _FilterRequest:
    """
    The minimal request surface `TypedCourseSearchBackend` and
    `CourseSearchFilterBackend` touch: `.GET` and `.query_params`. Building one lets
    the chat tools run the exact same search PCP's search bar runs, instead of a
    parallel implementation that would drift from it.
    """

    def __init__(self, params):
        query_dict = QueryDict(mutable=True)
        for key, value in params.items():
            if value is not None and value != "":
                query_dict[key] = str(value)
        query_dict._mutable = False
        self.GET = query_dict
        self.query_params = query_dict


def search_courses(
    *,
    semester,
    user=None,
    query=None,
    attributes=None,
    days=None,
    time=None,
    cu=None,
    activity=None,
    difficulty=None,
    course_quality=None,
    instructor_quality=None,
    is_open=None,
    rule_ids=None,
    sort_by=None,
    limit=None,
):
    """Search the course catalog for one semester. See `TOOLS` for parameter meaning."""
    limit = min(int(limit or SEARCH_DEFAULT_LIMIT), SEARCH_MAX_LIMIT)

    queryset = Course.with_reviews.filter(sections__isnull=False, semester=semester)

    request = _FilterRequest(
        {
            "search": query,
            "attributes": attributes,
            "days": days,
            "time": time,
            "cu": cu,
            "activity": activity,
            "difficulty": difficulty,
            "course_quality": course_quality,
            "instructor_quality": instructor_quality,
            "is_open": "true" if is_open else None,
            "rule_ids": rule_ids,
        }
    )

    # A fresh backend per call: TypedCourseSearchBackend memoizes the inferred search
    # type on `self`, so a reused instance would classify every later query as the first.
    for backend in (TypedCourseSearchBackend(), CourseSearchFilterBackend()):
        queryset = backend.filter_queryset(request, queryset, None)

    courses = list(queryset[:SEARCH_CANDIDATE_LIMIT])
    truncated = len(courses) == SEARCH_CANDIDATE_LIMIT

    if sort_by in ("course_quality", "instructor_quality"):
        courses.sort(key=lambda c: (getattr(c, sort_by) is None, -(getattr(c, sort_by) or 0)))
    elif sort_by in ("difficulty", "work_required"):
        courses.sort(key=lambda c: (getattr(c, sort_by) is None, getattr(c, sort_by) or 0))

    shortlist = courses[:limit]
    # Flag anything the student has already done, matched across crosslistings so the
    # graduate number of a course they took as an undergraduate does not read as new.
    history = course_history(user, semester)
    crosslistings = crosslistings_for([c.full_code for c in shortlist])

    results = []
    for course in shortlist:
        description = course.description or ""
        if len(description) > SEARCH_DESCRIPTION_CHARS:
            description = description[:SEARCH_DESCRIPTION_CHARS].rstrip() + "..."
        row = {
            "course_code": course.full_code,
            "title": course.title,
            "description": description,
            "credits": number(course.credits),
            "ratings": _course_ratings(course),
        }
        also = sorted(crosslistings.get(course.full_code) or ())
        if also:
            row["also_listed_as"] = also
        if course.full_code in history["completed"]:
            row["already_taken"] = True
        elif course.full_code in history["planned"]:
            row["already_planned"] = True
        results.append(row)

    return {
        "semester": semester,
        "num_results": len(results),
        "results": results,
        "note": (
            "Rows marked already_taken or already_planned are courses this student has "
            "done or lined up — including under a different crosslisted code. Do not "
            "recommend them as new options."
        ),
        # Ranking only saw the first SEARCH_CANDIDATE_LIMIT matches, so a "best rated"
        # answer over a truncated set is not actually the best. Say so.
        "truncated": truncated,
    }


def get_course(*, semester, course_code):
    """Full detail for one course in one semester, including every section."""
    course_code = course_code.strip().upper()

    course = (
        Course.with_reviews.filter(full_code=course_code, semester=semester)
        .prefetch_related(
            Prefetch(
                "sections",
                Section.objects.filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related("instructors", "meetings"),
            ),
            "attributes",
        )
        .first()
    )
    if course is None:
        other = list(
            Course.objects.filter(full_code=course_code)
            .order_by("-semester")
            .values_list("semester", flat=True)[:3]
        )
        if other:
            raise ToolError(
                f"{course_code} is not offered in {semester}. It was most recently "
                f"offered in {', '.join(other)}."
            )
        raise ToolError(
            f"No course with code {course_code} exists. Course codes look like "
            "CIS-1200; try search_courses to find the right code."
        )

    return {
        "course_code": course.full_code,
        "also_listed_as": sorted(c.full_code for c in course.crosslistings),
        "title": course.title,
        "semester": course.semester,
        "description": course.description,
        "credits": number(course.credits),
        "prerequisites": course.prerequisites or None,
        "syllabus_url": course.syllabus_url or None,
        "attributes": [
            {"code": a.code, "description": a.description} for a in course.attributes.all()
        ],
        "ratings": _course_ratings(course),
        "sections": [_section_row(s) for s in course.sections.all()],
    }


def get_course_reviews(*, semester, course_code):
    """
    Penn Course Review data for a course, aggregated across semesters and broken down
    by instructor. `semester` is unused — reviews span the course's whole history — but
    accepted so every tool has the same call signature.
    """
    del semester

    course_code = course_code.strip().upper()
    cache_key = f"pcp_chat_reviews:{course_code}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Imported here: review.views imports from courses at module scope, and courses
    # models import review helpers, so a top-level import cycles.
    from review.models import CachedReviewResponse
    from review.views import manual_course_reviews, most_recent_course_from_code

    try:
        recent_course = most_recent_course_from_code(course_code, None)
    except Course.DoesNotExist:
        raise ToolError(
            f"No review data found for {course_code}. Either the code is wrong or the "
            "course has never been offered with reviews."
        )

    # Reviews are keyed by topic (a course and its renumbered predecessors), and PCR
    # precomputes the expensive aggregation into CachedReviewResponse. Reuse that when
    # it is there; `manual_course_reviews` recomputes it from scratch otherwise.
    cached_response = None
    if recent_course.topic is not None:
        topic_id = ".".join(
            str(course_id)
            for course_id in sorted(recent_course.topic.courses.values_list("id", flat=True))
        )
        cached_response = CachedReviewResponse.objects.filter(topic_id=topic_id).first()
    reviews = (
        cached_response.response if cached_response else manual_course_reviews(course_code, None)
    )
    if not reviews:
        raise ToolError(f"No review data found for {course_code}.")

    instructors = sorted(
        reviews.get("instructors", {}).values(),
        key=lambda i: i.get("latest_semester") or "",
        reverse=True,
    )

    result = {
        "course_code": reviews.get("code", course_code),
        "title": reviews.get("name"),
        "latest_semester": reviews.get("latest_semester"),
        "num_semesters": reviews.get("num_semesters"),
        "ratings_all_semesters": _review_bits(reviews.get("average_reviews")),
        "ratings_most_recent_semester": _review_bits(reviews.get("recent_reviews")),
        "instructors": [
            {
                "name": instructor.get("name"),
                "latest_semester": instructor.get("latest_semester"),
                "num_semesters": instructor.get("num_semesters"),
                "ratings": _review_bits(instructor.get("average_reviews")),
            }
            for instructor in instructors[:10]
        ],
    }
    cache.set(cache_key, result, REVIEW_CACHE_TTL)
    return result


def _truncate(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text or None
    return text[:limit].rstrip() + "..."


def _preview(course_code, title=None, credits=None, ratings=None, description=None):
    return {
        "course_code": course_code,
        "title": title,
        "credits": credits,
        "ratings": ratings,
        "description": _truncate(description, PREVIEW_DESCRIPTION_CHARS),
    }


def enrich_previews(previews):
    """
    Fill gaps in the blurbs from the catalog, in one query.

    Which fields a blurb arrives with depends on which tool surfaced the course. A
    catalog lookup carries ratings and a description; the schedule and degree-plan
    tools report what is *in the plan*, so they carry neither. Left alone, a course the
    assistant only saw in the student's cart would render a blurb saying it has no Penn
    Course Review data — when the truth is only that nobody looked it up.

    Mutates `previews` in place, filling missing fields and never overwriting one a
    tool already supplied. Every blurb for a course that exists comes out with the full
    set of keys, so a caller can tell "no ratings" from "never filled in".

    Returns the codes it could not find in the catalog.
    """
    if not previews:
        return set()

    best = {}
    for course in Course.with_reviews.filter(full_code__in=list(previews)).order_by(
        "full_code", "-semester"
    ):
        # Most recent offering wins: its title, credits and description are current.
        best.setdefault(course.full_code, course)

    for code, course in best.items():
        found = _preview(
            code,
            title=course.title,
            credits=number(course.credits),
            ratings=_course_ratings(course),
            description=course.description,
        )
        target = previews[code]
        for key, value in found.items():
            if target.get(key) is None:
                target[key] = value

    return set(previews) - set(best)


def collect_previews(tool_name, result):
    """
    Pull course blurbs out of a tool result.

    The assistant only names courses it has looked up, so these cover everything its
    reply can mention. `run_chat_turn` narrows them to the codes that appear in the
    reply and returns those, which lets the client render a preview card per course
    code with no second round trip — and guarantees the card says the same thing the
    model was told.
    """
    if not isinstance(result, dict):
        return []

    if tool_name == "search_courses":
        return [
            _preview(
                row["course_code"],
                title=row.get("title"),
                credits=row.get("credits"),
                ratings=row.get("ratings"),
                description=row.get("description"),
            )
            for row in result.get("results", [])
        ]

    if tool_name == "get_course":
        return [
            _preview(
                result["course_code"],
                title=result.get("title"),
                credits=result.get("credits"),
                ratings=result.get("ratings"),
                description=result.get("description"),
            )
        ]

    if tool_name in ("get_my_schedules", "add_to_schedule", "remove_from_schedule"):
        schedules = result.get("schedules") or [result.get("schedule")]
        return [
            _preview(
                row["course_code"],
                title=row.get("title"),
                credits=row.get("credits"),
            )
            for schedule in schedules
            if schedule
            for row in schedule.get("sections", [])
        ]

    if tool_name == "get_my_degree_plan":
        return [
            _preview(row["full_code"], title=row.get("title"), credits=row.get("credits"))
            for plan in result.get("degree_plans", [])
            for key in ("courses_completed", "courses_planned", "courses_without_a_semester")
            for row in plan.get(key, [])
        ]

    if tool_name == "get_course_reviews":
        return [
            _preview(
                result["course_code"],
                title=result.get("title"),
                ratings=result.get("ratings_all_semesters"),
            )
        ]

    return []


CATALOG_TOOL_IMPLEMENTATIONS = {
    "search_courses": search_courses,
    "get_course": get_course,
    "get_course_reviews": get_course_reviews,
}

TOOL_IMPLEMENTATIONS = {
    **CATALOG_TOOL_IMPLEMENTATIONS,
    **PLAN_TOOL_IMPLEMENTATIONS,
    **DEGREE_TOOL_IMPLEMENTATIONS,
}

# Only these reach the student's own data, and only these are handed the user. A
# catalog tool has no way to ask who is asking.
# Tools handed the authenticated user. Search is here so it can mark courses the
# student has already taken; the rest read or write their own data.
USER_SCOPED_TOOLS = (
    set(PLAN_TOOL_IMPLEMENTATIONS) | set(DEGREE_TOOL_IMPLEMENTATIONS) | {"search_courses"}
)


CATALOG_TOOLS = [
    {
        "name": "search_courses",
        "description": (
            "Search Penn's course catalog for one semester. This is the same search that "
            "powers the PCP search bar. `query` matches course codes, titles, and "
            "instructor names; the other parameters filter the results. Returns a "
            "shortened description per course — call get_course for the full text and "
            "for section meeting times."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Free-text search: a course code fragment ('CIS', 'CIS-1200'), a "
                        "keyword from the title, or an instructor name. Omit to browse "
                        "purely by filter."
                    ),
                },
                "semester": {
                    "type": "string",
                    "description": (
                        "Semester as YYYYx, e.g. 2024C for fall 2024. Defaults to the "
                        "student's current planning semester."
                    ),
                },
                "attributes": {
                    "type": "string",
                    "description": (
                        "Attribute codes combined with * (and) and | (or), optionally "
                        "parenthesized, e.g. 'WUOM' or '(EMCI|EMCN)*WUOM'. Attribute "
                        "codes encode requirements like sectors and foundational "
                        "approaches."
                    ),
                },
                "days": {
                    "type": "string",
                    "description": (
                        "Restrict to courses that only meet on these days, as a subset of "
                        "'MTWRFSU' (R is Thursday), e.g. 'TR' for Tuesday/Thursday only."
                    ),
                },
                "time": {
                    "type": "string",
                    "description": (
                        "Restrict to courses meeting inside this time window, as "
                        "'start-end' in 24-hour decimal hours, e.g. '11.5-17' for 11:30 "
                        "AM to 5:00 PM."
                    ),
                },
                "cu": {
                    "type": "string",
                    "description": (
                        "Comma-separated course-unit values to include, e.g. '1' or " "'0.5,1'."
                    ),
                },
                "activity": {
                    "type": "string",
                    "description": (
                        "Comma-separated section activity codes, e.g. 'LEC' for lecture, "
                        "'SEM' for seminar, 'REC' for recitation, 'LAB' for lab."
                    ),
                },
                "difficulty": {
                    "type": "string",
                    "description": (
                        "Keep courses whose average difficulty falls in this range, as "
                        "'min-max' on a 0-4 scale, e.g. '0-2.5'. Unrated courses pass "
                        "every rating filter rather than being hidden, so results can "
                        "include courses with no ratings at all — check each course's "
                        "`ratings` before describing a result as meeting the range."
                    ),
                },
                "course_quality": {
                    "type": "string",
                    "description": (
                        "Course quality range as 'min-max' on a 0-4 scale. Unrated "
                        "courses pass, as with difficulty."
                    ),
                },
                "instructor_quality": {
                    "type": "string",
                    "description": (
                        "Instructor quality range as 'min-max' on a 0-4 scale. Unrated "
                        "courses pass, as with difficulty."
                    ),
                },
                "is_open": {
                    "type": "boolean",
                    "description": (
                        "If true, only courses with at least one section currently open "
                        "for registration."
                    ),
                },
                "rule_ids": {
                    "type": "string",
                    "description": (
                        "Keep only courses that satisfy these degree requirements, as "
                        "comma-separated rule ids. Take these from the "
                        "`searchable_with.rule_ids` on an unsatisfied requirement in "
                        "get_my_degree_plan. Several ids are ANDed, so a course must "
                        "satisfy all of them."
                    ),
                },
                "sort_by": {
                    "type": "string",
                    "enum": [
                        "course_quality",
                        "instructor_quality",
                        "difficulty",
                        "work_required",
                    ],
                    "description": (
                        "Rank results by this field — quality descending, difficulty and "
                        "work ascending. Unrated courses sort last. Defaults to course "
                        "code order."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": (
                        f"How many courses to return, up to {SEARCH_MAX_LIMIT}. Defaults "
                        f"to {SEARCH_DEFAULT_LIMIT}."
                    ),
                },
            },
        },
    },
    {
        "name": "get_course",
        "description": (
            "Full detail for one course in one semester: the complete description, "
            "prerequisites, attributes, review averages, and every section with its "
            "instructors, meeting times, and registration status. Use this before "
            "telling a student when a course meets or who teaches it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "Full course code, e.g. 'CIS-1200'.",
                },
                "semester": {
                    "type": "string",
                    "description": (
                        "Semester as YYYYx. Defaults to the student's current planning " "semester."
                    ),
                },
            },
            "required": ["course_code"],
        },
    },
    {
        "name": "get_course_reviews",
        "description": (
            "Penn Course Review ratings for a course, averaged across every semester "
            "it has been taught and broken down by instructor. Use this when the "
            "student asks who to take a course with, or how a course's ratings have "
            "changed. Ratings are 0-4."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "Full course code, e.g. 'CIS-1200'.",
                },
            },
            "required": ["course_code"],
        },
    },
]


def run_tool(name, tool_input, *, semester, user):
    """
    Dispatch one tool call. Raises ToolError for anything the model can recover from
    by calling a different tool or asking the student a question.
    """
    implementation = TOOL_IMPLEMENTATIONS.get(name)
    if implementation is None:
        raise ToolError(f"No such tool: {name}")

    kwargs = dict(tool_input or {})
    # Identity is never taken from the model. Whatever it sent under this name is
    # dropped, and user-scoped tools are given the authenticated user instead.
    kwargs.pop("user", None)
    if name in USER_SCOPED_TOOLS:
        kwargs["user"] = user
    # The model may name a semester per call; otherwise it inherits the student's.
    kwargs["semester"] = kwargs.get("semester") or semester

    try:
        return implementation(**kwargs)
    except ToolError:
        raise
    except TypeError as e:
        raise ToolError(f"Invalid arguments for {name}: {e}")


TOOLS = CATALOG_TOOLS + PLAN_TOOLS + DEGREE_TOOLS
