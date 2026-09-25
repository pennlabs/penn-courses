"""Pure, network-free course-planning logic.

Everything here operates on plain dicts (the shapes returned by the Penn Courses
API) and primitives, so it is trivially unit-testable without mocking HTTP.

Conventions from the upstream API:
- Meeting times use Penn's ``HH.MM`` float encoding: the integer part is the
  24-hour hour and the two decimal digits are literal minutes. So ``10.15`` ->
  10:15, ``15.3`` -> 15:30, ``12.59`` -> 12:59. (This ordering is chronological,
  so raw float comparison is safe for overlap detection.)
- Day codes are single letters: M, T, W, R (Thursday), F, and occasionally
  S (Saturday) / U (Sunday).
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable


DAY_NAMES: dict[str, str] = {
    "M": "Monday",
    "T": "Tuesday",
    "W": "Wednesday",
    "R": "Thursday",
    "F": "Friday",
    "S": "Saturday",
    "U": "Sunday",
}
DAY_ORDER = ["M", "T", "W", "R", "F", "S", "U"]


def fmt_time(value: float | int | None) -> str:
    """Format Penn's ``HH.MM`` float time as a 24h ``HH:MM`` string.

    The two decimal digits are literal minutes: ``10.15`` -> ``"10:15"``,
    ``15.3`` -> ``"15:30"``, ``12.0`` -> ``"12:00"``. Returns ``"TBA"`` for
    missing values.
    """
    if value is None:
        return "TBA"
    hours = int(value)
    minutes = round((float(value) - hours) * 100)
    return f"{hours:02d}:{minutes:02d}"


def fmt_meeting(meeting: dict[str, Any]) -> str:
    """Render a single meeting dict as e.g. ``"Monday 10:00-11:30 (Towne 100)"``."""
    day = DAY_NAMES.get(meeting.get("day", ""), meeting.get("day", "?"))
    start = fmt_time(meeting.get("start"))
    end = fmt_time(meeting.get("end"))
    room = meeting.get("room")
    base = f"{day} {start}-{end}"
    return f"{base} ({room})" if room else base


def meetings_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True if two meetings fall on the same day with overlapping time ranges.

    Uses strict inequality so that back-to-back meetings (one ending exactly when
    the next begins) are *not* treated as a conflict.
    """
    if a.get("day") != b.get("day"):
        return False
    a_start, a_end = a.get("start"), a.get("end")
    b_start, b_end = b.get("start"), b.get("end")
    if None in (a_start, a_end, b_start, b_end):
        return False  # cannot judge a TBA meeting
    return a_start < b_end and b_start < a_end


def _section_meetings(section: dict[str, Any]) -> list[dict[str, Any]]:
    return section.get("meetings") or []


def detect_conflicts(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find all pairwise time conflicts among a candidate set of sections.

    Each ``section`` dict must contain ``id`` (or ``section_id``) and ``meetings``.
    Returns a list of conflict records describing the two clashing meetings.
    """
    conflicts: list[dict[str, Any]] = []
    for sec_a, sec_b in combinations(sections, 2):
        id_a = sec_a.get("id") or sec_a.get("section_id", "?")
        id_b = sec_b.get("id") or sec_b.get("section_id", "?")
        for m_a in _section_meetings(sec_a):
            for m_b in _section_meetings(sec_b):
                if meetings_overlap(m_a, m_b):
                    conflicts.append(
                        {
                            "section_a": id_a,
                            "section_b": id_b,
                            "day": DAY_NAMES.get(m_a.get("day", ""), m_a.get("day")),
                            "meeting_a": fmt_meeting(m_a),
                            "meeting_b": fmt_meeting(m_b),
                        }
                    )
    return conflicts


def weekly_grid(sections: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group section meetings into a day-keyed, time-sorted weekly grid."""
    grid: dict[str, list[dict[str, Any]]] = {DAY_NAMES[d]: [] for d in DAY_ORDER}
    for section in sections:
        sec_id = section.get("id") or section.get("section_id", "?")
        for m in _section_meetings(section):
            day = DAY_NAMES.get(m.get("day", ""))
            if day is None:
                continue
            grid[day].append(
                {
                    "section": sec_id,
                    "start": fmt_time(m.get("start")),
                    "end": fmt_time(m.get("end")),
                    "room": m.get("room"),
                    "_sort": m.get("start") if m.get("start") is not None else 99,
                }
            )
    for day in grid:
        grid[day].sort(key=lambda x: x["_sort"])
        for entry in grid[day]:
            entry.pop("_sort", None)
    # drop empty days for a tidier result
    return {day: entries for day, entries in grid.items() if entries}


def missing_associated_warnings(
    sections: list[dict[str, Any]],
) -> list[str]:
    """Warn when a section lists required ``associated_sections`` that are absent.

    Many Penn lectures require a co-registered recitation/lab; the API exposes
    these via ``associated_sections``. We flag a lecture whose companions are not
    present in the chosen set.
    """
    chosen_ids = {s.get("id") or s.get("section_id") for s in sections}
    warnings: list[str] = []
    for section in sections:
        sec_id = section.get("id") or section.get("section_id", "?")
        associated = section.get("associated_sections") or []
        present = [a for a in associated if a.get("id") in chosen_ids]
        if associated and not present:
            options = ", ".join(f"{a.get('id')} ({a.get('activity')})" for a in associated)
            warnings.append(
                f"{sec_id} typically requires a companion section; none selected. "
                f"Options: {options}"
            )
    return warnings


def build_schedule(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble a weekly schedule summary from a set of section dicts.

    Returns total credits, the weekly grid, time conflicts, and warnings for
    missing required companion sections.
    """
    total_credits = 0.0
    for s in sections:
        try:
            total_credits += float(s.get("credits") or 0)
        except (TypeError, ValueError):
            pass
    conflicts = detect_conflicts(sections)
    return {
        "sections": [s.get("id") or s.get("section_id") for s in sections],
        "total_credits": round(total_credits, 2),
        "weekly_grid": weekly_grid(sections),
        "conflicts": conflicts,
        "has_conflicts": bool(conflicts),
        "warnings": missing_associated_warnings(sections),
    }


def compare_courses(details: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a side-by-side comparison table from full course-detail dicts."""
    fields = [
        "title",
        "credits",
        "course_quality",
        "instructor_quality",
        "difficulty",
        "work_required",
        "num_sections",
        "prerequisites",
    ]
    rows: list[dict[str, Any]] = []
    for d in details:
        row = {"course": d.get("id")}
        for f in fields:
            if f == "num_sections":
                row[f] = d.get("num_sections") or len(d.get("sections") or [])
            else:
                row[f] = d.get(f)
        rows.append(row)
    return {"courses": [d.get("id") for d in details], "comparison": rows}


def _course_matches(course: dict[str, Any], target: str, match: str) -> bool:
    target_l = target.lower()
    attributes = course.get("attributes") or []
    pre_ngss = course.get("pre_ngss_requirements") or []
    haystacks: list[str] = []
    for attr in attributes:
        if match == "code":
            haystacks.append(str(attr.get("code", "")))
        else:  # "description"
            haystacks.append(str(attr.get("description", "")))
            haystacks.append(str(attr.get("code", "")))
    for req in pre_ngss:
        haystacks.append(str(req.get("code", "")))
        haystacks.append(str(req.get("name", "")))
    if match == "code":
        return any(target_l == h.lower() for h in haystacks)
    return any(target_l in h.lower() for h in haystacks)


def filter_courses_by_attribute(
    courses: Iterable[dict[str, Any]], target: str, match: str = "code"
) -> list[dict[str, Any]]:
    """Client-side filter over course ``attributes`` / ``pre_ngss_requirements``.

    ``match="code"`` requires an exact attribute-code match; ``match="description"``
    does a case-insensitive substring search across codes and descriptions.
    """
    return [c for c in courses if _course_matches(c, target, match)]
