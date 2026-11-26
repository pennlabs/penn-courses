import pytest

from penn_course_mcp.planning import (
    build_schedule,
    compare_courses,
    detect_conflicts,
    filter_courses_by_attribute,
    fmt_time,
    meetings_overlap,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (10.15, "10:15"),
        (11.14, "11:14"),
        (15.3, "15:30"),
        (12.0, "12:00"),
        (12.59, "12:59"),
        (9.0, "09:00"),
        (19.59, "19:59"),
        (None, "TBA"),
    ],
)
def test_fmt_time(value, expected):
    assert fmt_time(value) == expected


def m(day, start, end, room="X"):
    return {"day": day, "start": start, "end": end, "room": room}


def test_meetings_overlap_same_time_same_day():
    assert meetings_overlap(m("M", 10.0, 11.0), m("M", 10.3, 10.45)) is True


def test_meetings_overlap_touching_is_not_conflict():
    # one ends exactly when the next begins -> NOT a conflict (strict <)
    assert meetings_overlap(m("M", 10.0, 11.0), m("M", 11.0, 12.0)) is False


def test_meetings_overlap_disjoint():
    assert meetings_overlap(m("M", 10.0, 11.0), m("M", 13.0, 14.0)) is False


def test_meetings_overlap_different_day():
    assert meetings_overlap(m("M", 10.0, 11.0), m("T", 10.0, 11.0)) is False


def test_meetings_overlap_tba_is_not_conflict():
    assert meetings_overlap(m("M", None, None), m("M", 10.0, 11.0)) is False


def test_detect_conflicts_three_sections_one_overlap():
    sections = [
        {"id": "A-001", "meetings": [m("M", 10.0, 11.0)]},
        {"id": "B-001", "meetings": [m("M", 10.3, 11.3)]},  # conflicts with A
        {"id": "C-001", "meetings": [m("T", 10.0, 11.0)]},  # no conflict
    ]
    conflicts = detect_conflicts(sections)
    assert len(conflicts) == 1
    pair = {conflicts[0]["section_a"], conflicts[0]["section_b"]}
    assert pair == {"A-001", "B-001"}


def test_build_schedule_credits_and_grid():
    sections = [
        {"id": "A-001", "credits": 1.0, "meetings": [m("M", 9.0, 10.0)]},
        {"id": "B-001", "credits": 0.5, "meetings": [m("W", 13.3, 14.3)]},
    ]
    result = build_schedule(sections)
    assert result["total_credits"] == 1.5
    assert result["has_conflicts"] is False
    assert "Monday" in result["weekly_grid"]
    assert result["weekly_grid"]["Monday"][0]["start"] == "09:00"


def test_build_schedule_missing_associated_warning():
    sections = [
        {
            "id": "CIS-1200-001",
            "credits": 1.0,
            "meetings": [m("M", 10.0, 11.0)],
            "associated_sections": [{"id": "CIS-1200-201", "activity": "REC"}],
        }
    ]
    result = build_schedule(sections)
    assert result["warnings"]
    assert "CIS-1200-201" in result["warnings"][0]


def test_build_schedule_associated_satisfied_no_warning():
    sections = [
        {
            "id": "CIS-1200-001",
            "credits": 1.0,
            "meetings": [m("M", 10.0, 11.0)],
            "associated_sections": [{"id": "CIS-1200-201", "activity": "REC"}],
        },
        {"id": "CIS-1200-201", "credits": 0.0, "meetings": [m("F", 14.0, 15.0)]},
    ]
    result = build_schedule(sections)
    assert result["warnings"] == []


def test_compare_courses():
    details = [
        {"id": "CIS-1200", "title": "PL I", "course_quality": 2.8, "credits": 1.0},
        {"id": "CIS-1600", "title": "Math Found", "course_quality": 3.1, "credits": 1.0},
    ]
    result = compare_courses(details)
    assert result["courses"] == ["CIS-1200", "CIS-1600"]
    assert len(result["comparison"]) == 2


def test_filter_courses_by_attribute_code():
    courses = [
        {"id": "A", "attributes": [{"code": "EUMS", "description": "Euro studies"}]},
        {"id": "B", "attributes": [{"code": "MFR", "description": "Formal reasoning"}]},
    ]
    assert [c["id"] for c in filter_courses_by_attribute(courses, "MFR")] == ["B"]


def test_filter_courses_by_attribute_description_substring():
    courses = [
        {"id": "A", "attributes": [{"code": "EUMS", "description": "Euro studies"}]},
        {"id": "B", "attributes": [{"code": "MFR", "description": "Formal reasoning"}]},
    ]
    matched = filter_courses_by_attribute(courses, "reasoning", match="description")
    assert [c["id"] for c in matched] == ["B"]
