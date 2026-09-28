"""FastMCP server exposing Penn course-planning tools.

Run with stdio (default) or streamable HTTP:

    penn-course-mcp                       # stdio
    penn-course-mcp --transport http      # HTTP at http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from . import __version__
from .client import PennCoursesClient
from .config import Settings
from .errors import (
    CourseNotFound,
    PennCoursesError,
    ReviewAuthRequired,
    UpstreamError,
    WriteAuthRequired,
)
from .planning import build_schedule as _build_schedule
from .planning import compare_courses as _compare_courses
from .planning import detect_conflicts as _detect_conflicts
from .planning import filter_courses_by_attribute, fmt_meeting


mcp = FastMCP(
    name="penn-course-mcp",
    instructions=(
        "Tools for planning courses at the University of Pennsylvania using the "
        "public Penn Courses (Penn Course Plan / Review) API. Use search_courses to "
        "discover courses, get_course_details for full info, and the schedule tools "
        "to detect time conflicts and assemble a weekly plan. Course codes look like "
        "'CIS-1200'; section ids look like 'CIS-1200-001'. Ratings range roughly 0-4 "
        "(higher course_quality/instructor_quality is better; lower difficulty and "
        "work_required is lighter)."
    ),
)

_client: PennCoursesClient | None = None


def get_client() -> PennCoursesClient:
    global _client
    if _client is None:
        _client = PennCoursesClient(Settings.from_env())
    return _client


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _err(exc: Exception) -> dict[str, Any]:
    """Translate an exception into a friendly, structured tool result."""
    if isinstance(exc, CourseNotFound):
        return {
            "error": str(exc),
            "hint": "Check the course code (e.g. 'CIS-1200') and semester.",
        }
    if isinstance(exc, ReviewAuthRequired):
        return {
            "error": str(exc),
            "hint": "Set PENN_COURSES_SESSION_COOKIE to enable detailed reviews.",
        }
    if isinstance(exc, WriteAuthRequired):
        return {
            "error": str(exc),
            "hint": (
                "Saving schedules requires a logged-in Penn session. Set "
                "PENN_COURSES_SESSION_COOKIE to include both sessionid and csrftoken."
            ),
        }
    if isinstance(exc, (UpstreamError, PennCoursesError)):
        return {"error": str(exc), "hint": "The Penn Courses API may be unavailable."}
    return {"error": f"Unexpected error: {exc}"}


def _section_to_course_code(section_id: str) -> str:
    """'CIS-1200-001' -> 'CIS-1200'."""
    return section_id.rsplit("-", 1)[0].upper()


def _summarize_section(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": section.get("id"),
        "activity": section.get("activity"),
        "status": section.get("status"),
        "credits": section.get("credits"),
        "capacity": section.get("capacity"),
        "registration_volume": section.get("registration_volume"),
        "instructors": [i.get("name") for i in section.get("instructors") or []],
        "meetings": [fmt_meeting(m) for m in section.get("meetings") or []],
        "associated_sections": [
            {"id": a.get("id"), "activity": a.get("activity")}
            for a in section.get("associated_sections") or []
        ],
    }


async def _resolve_section_dicts(
    semester: str | None, section_ids: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fetch the section dicts named by ``section_ids`` from their parent courses.

    Returns (found_sections, not_found_ids).
    """
    client = get_client()
    wanted = {sid.upper() for sid in section_ids}
    by_course: dict[str, list[str]] = {}
    for sid in wanted:
        by_course.setdefault(_section_to_course_code(sid), []).append(sid)

    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for course_code in by_course:
        try:
            course = await client.get_course(semester, course_code)
        except CourseNotFound:
            continue
        for section in course.get("sections") or []:
            sid = str(section.get("id", "")).upper()
            if sid in wanted and sid not in seen:
                # carry credits down from the course if the section omits them
                section = {**section}
                section.setdefault("credits", course.get("credits"))
                found.append(section)
                seen.add(sid)
    not_found = sorted(wanted - seen)
    return found, not_found


# --------------------------------------------------------------------------
# tools — discovery & detail
# --------------------------------------------------------------------------
@mcp.tool
async def get_current_semester() -> dict[str, Any]:
    """Return the active semester and whether detailed reviews are enabled.

    Useful as a first call to learn the current term code (e.g. '2026C') and the
    server's review-auth status.
    """
    client = get_client()
    try:
        options = await client.get_options()
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {
        "semester": options.get("SEMESTER"),
        "registration_open": options.get("REGISTRATION_OPEN"),
        "reviews_enabled": client.settings.reviews_enabled,
    }


@mcp.tool
async def search_courses(
    query: str, semester: str | None = None, limit: int = 25
) -> dict[str, Any]:
    """Search the course catalog by code or keyword (e.g. 'CIS-1200' or 'ethics').

    Returns lightweight course summaries including aggregate ratings. ``semester``
    defaults to the current term.
    """
    client = get_client()
    try:
        results = await client.search_courses(semester, query)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {
        "count": len(results),
        "results": results[: max(0, limit)],
    }


@mcp.tool
async def get_course_details(course_code: str, semester: str | None = None) -> dict[str, Any]:
    """Get full details for a course: description, prerequisites, attributes,
    crosslistings, aggregate ratings, and all sections with meeting times.
    """
    client = get_client()
    try:
        course = await client.get_course(semester, course_code)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    course = {**course}
    course["sections"] = [_summarize_section(s) for s in course.get("sections") or []]
    return course


@mcp.tool
async def list_course_sections(
    course_code: str,
    semester: str | None = None,
    open_only: bool = False,
    activity: str | None = None,
) -> dict[str, Any]:
    """List a course's sections with formatted meeting times and instructors.

    ``open_only`` keeps only sections whose status is open; ``activity`` filters by
    type (e.g. 'LEC', 'REC', 'LAB').
    """
    client = get_client()
    try:
        course = await client.get_course(semester, course_code)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    sections = course.get("sections") or []
    if open_only:
        sections = [s for s in sections if str(s.get("status", "")).upper() == "O"]
    if activity:
        sections = [s for s in sections if str(s.get("activity", "")).upper() == activity.upper()]
    return {
        "course": course.get("id"),
        "count": len(sections),
        "sections": [_summarize_section(s) for s in sections],
    }


# --------------------------------------------------------------------------
# tools — ratings & reviews
# --------------------------------------------------------------------------
@mcp.tool
async def get_course_ratings(course_code: str, semester: str | None = None) -> dict[str, Any]:
    """Return the public aggregate ratings for a course (always available).

    Includes course_quality, instructor_quality, difficulty, and work_required.
    """
    client = get_client()
    try:
        course = await client.get_course(semester, course_code)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {
        "course": course.get("id"),
        "course_quality": course.get("course_quality"),
        "instructor_quality": course.get("instructor_quality"),
        "difficulty": course.get("difficulty"),
        "work_required": course.get("work_required"),
        "credits": course.get("credits"),
    }


@mcp.tool
async def get_course_reviews(course_code: str) -> dict[str, Any]:
    """Get detailed Penn Course Review breakdowns for a course.

    When an authenticated session cookie is configured this returns the full
    per-instructor review data. Otherwise it gracefully falls back to the public
    aggregate ratings and reports an unauthenticated status (never errors).
    """
    client = get_client()
    try:
        data = await client.get_review(course_code)
        return {"auth_status": "authenticated", "reviews": data}
    except ReviewAuthRequired:
        # graceful degradation to public aggregates
        try:
            course = await client.get_course(None, course_code)
        except Exception as exc:  # noqa: BLE001
            return _err(exc)
        return {
            "auth_status": "unauthenticated",
            "note": (
                "Detailed reviews require authentication; returning public aggregate "
                "ratings instead. Set PENN_COURSES_SESSION_COOKIE to unlock full reviews."
            ),
            "course": course.get("id"),
            "aggregate_ratings": {
                "course_quality": course.get("course_quality"),
                "instructor_quality": course.get("instructor_quality"),
                "difficulty": course.get("difficulty"),
                "work_required": course.get("work_required"),
            },
        }
    except Exception as exc:  # noqa: BLE001
        return _err(exc)


# --------------------------------------------------------------------------
# tools — requirement / attribute discovery
# --------------------------------------------------------------------------
@mcp.tool
async def find_courses_by_attribute(
    attribute: str,
    semester: str | None = None,
    match: str = "code",
    prefilter_query: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Find courses carrying a given attribute (e.g. 'EUMS', 'MFR', a Gen-Ed code).

    ``match='code'`` requires an exact attribute-code match; ``match='description'``
    does a substring search across codes and descriptions. Supply ``prefilter_query``
    to narrow the candidate set first (faster, smaller payload).
    """
    client = get_client()
    try:
        if prefilter_query:
            candidates = await client.search_courses(semester, prefilter_query)
            # search results lack attributes; fetch detail for each candidate
            detailed = []
            for c in candidates[:200]:
                try:
                    detailed.append(await client.get_course(semester, c["id"]))
                except CourseNotFound:
                    continue
            candidates = detailed
        else:
            candidates = await client.list_all_courses(semester)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    matched = filter_courses_by_attribute(candidates, attribute, match=match)
    return {
        "attribute": attribute,
        "match": match,
        "count": len(matched),
        "results": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "attributes": [a.get("code") for a in c.get("attributes") or []],
            }
            for c in matched[: max(0, limit)]
        ],
    }


@mcp.tool
async def find_courses_by_requirement(
    requirement: str, semester: str | None = None, limit: int = 50
) -> dict[str, Any]:
    """Find courses fulfilling a requirement (pre-NGSS requirement code or name).

    Substring-matches against course attributes and pre-NGSS requirement codes/names.
    """
    client = get_client()
    try:
        candidates = await client.list_all_courses(semester)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    matched = filter_courses_by_attribute(candidates, requirement, match="description")
    return {
        "requirement": requirement,
        "count": len(matched),
        "results": [{"id": c.get("id"), "title": c.get("title")} for c in matched[: max(0, limit)]],
    }


# --------------------------------------------------------------------------
# tools — planning utilities
# --------------------------------------------------------------------------
@mcp.tool
async def check_schedule_conflicts(
    sections: list[str], semester: str | None = None
) -> dict[str, Any]:
    """Check a set of section ids (e.g. ['CIS-1200-001','MATH-1400-002']) for time
    conflicts. Returns the clashing meetings in human-readable form.
    """
    try:
        found, not_found = await _resolve_section_dicts(semester, sections)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    conflicts = _detect_conflicts(found)
    return {
        "requested": sections,
        "not_found": not_found,
        "has_conflicts": bool(conflicts),
        "conflicts": conflicts,
    }


@mcp.tool
async def build_schedule(sections: list[str], semester: str | None = None) -> dict[str, Any]:
    """Assemble a weekly schedule from section ids: total credits, a day-by-day
    grid, time conflicts, and warnings for missing required companion sections.
    """
    try:
        found, not_found = await _resolve_section_dicts(semester, sections)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    result = _build_schedule(found)
    result["not_found"] = not_found
    return result


@mcp.tool
async def compare_courses(course_codes: list[str], semester: str | None = None) -> dict[str, Any]:
    """Compare courses side by side on ratings, difficulty, workload, credits, and
    prerequisites. Accepts a list of course codes (e.g. ['CIS-1200','CIS-1600']).
    """
    client = get_client()
    details: list[dict[str, Any]] = []
    not_found: list[str] = []
    for code in course_codes:
        try:
            details.append(await client.get_course(semester, code))
        except CourseNotFound:
            not_found.append(code.upper())
        except Exception as exc:  # noqa: BLE001
            return _err(exc)
    result = _compare_courses(details)
    result["not_found"] = not_found
    return result


@mcp.tool
async def recommend_courses(
    query: str,
    semester: str | None = None,
    sort_by: str = "course_quality",
    limit: int = 10,
) -> dict[str, Any]:
    """Search and rank courses by a quality metric.

    ``sort_by`` is one of: 'course_quality', 'instructor_quality',
    'recommendation_score' (higher is better), or 'difficulty' / 'work_required'
    (lower is better, for finding lighter courses).
    """
    client = get_client()
    try:
        results = await client.search_courses(semester, query)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ascending = sort_by in ("difficulty", "work_required")
    valid_keys = {
        "course_quality",
        "instructor_quality",
        "recommendation_score",
        "difficulty",
        "work_required",
    }
    if sort_by not in valid_keys:
        sort_by = "course_quality"

    def key(c: dict[str, Any]) -> float:
        val = c.get(sort_by)
        if val is None:
            # push unrated courses to the end regardless of direction
            return float("inf") if ascending else float("-inf")
        return float(val)

    ranked = sorted(results, key=key, reverse=not ascending)
    return {
        "query": query,
        "sort_by": sort_by,
        "order": "ascending" if ascending else "descending",
        "results": ranked[: max(0, limit)],
    }


# --------------------------------------------------------------------------
# tools — Penn Course Plan schedule writes (authenticated)
# --------------------------------------------------------------------------
@mcp.tool
async def list_schedules() -> dict[str, Any]:
    """List the saved schedules in your Penn Course Plan account (requires auth).

    Returns each schedule's id, name, semester, and the section ids it contains —
    handy for finding a ``schedule_id`` to update or delete.
    """
    client = get_client()
    try:
        schedules = await client.list_schedules()
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {
        "count": len(schedules),
        "schedules": [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "semester": s.get("semester"),
                "sections": [sec.get("id") for sec in s.get("sections") or []],
            }
            for s in schedules
        ],
    }


@mcp.tool
async def save_schedule(
    name: str,
    sections: list[str],
    semester: str | None = None,
    schedule_id: int | None = None,
) -> dict[str, Any]:
    """Save a schedule to your Penn Course Plan account so it appears on the website.

    Creates a new schedule named ``name`` containing the given ``sections`` (full
    section ids like 'CIS-1200-001'). Pass an existing ``schedule_id`` to overwrite
    that schedule instead of creating a new one. **Writes to your live Penn account**
    and requires PENN_COURSES_SESSION_COOKIE (sessionid + csrftoken).
    """
    client = get_client()
    try:
        result = await client.save_schedule(
            name=name,
            semester=semester,
            section_ids=sections,
            schedule_id=schedule_id,
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {
        "saved": True,
        "action": "updated" if schedule_id is not None else "created",
        "schedule_id": result.get("id", schedule_id),
        "name": name,
        "sections": [s.upper() for s in sections],
        "note": "Refresh penncourseplan.com and select this schedule to see it.",
    }


@mcp.tool
async def delete_schedule(schedule_id: int) -> dict[str, Any]:
    """Delete a saved Penn Course Plan schedule by its id (requires auth).

    Use ``list_schedules`` to find the id first. This permanently removes the
    schedule from your Penn Course Plan account.
    """
    client = get_client()
    try:
        await client.delete_schedule(schedule_id)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return {"deleted": True, "schedule_id": schedule_id}


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------
def cli() -> None:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        prog="penn-course-mcp",
        description="MCP server for Penn course planning.",
    )
    parser.add_argument("--version", action="version", version=f"penn-course-mcp {__version__}")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.getenv("PENN_COURSES_TRANSPORT", "stdio"),
        help="Transport to serve (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("PENN_COURSES_HOST", "127.0.0.1"),
        help="Host for HTTP transport (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PENN_COURSES_PORT", "8000")),
        help="Port for HTTP transport (default: 8000).",
    )
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    cli()
