import httpx
import pytest
import respx

import penn_course_mcp.server as server
from penn_course_mcp.client import PennCoursesClient
from penn_course_mcp.config import Settings


BASE = "https://penncoursereview.com"


@pytest.fixture
def wire_client(monkeypatch):
    """Point the server's global client at a respx-mockable instance."""

    def _make(session_cookie=None):
        settings = Settings(base_url=BASE, semester="current", session_cookie=session_cookie)
        client = PennCoursesClient(settings)
        monkeypatch.setattr(server, "_client", client)
        return client

    return _make


@pytest.mark.asyncio
@respx.mock
async def test_get_current_semester(wire_client, options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    wire_client()
    out = await server.get_current_semester()
    assert out["semester"] == options_fixture["SEMESTER"]
    assert out["reviews_enabled"] is False


@pytest.mark.asyncio
@respx.mock
async def test_search_courses_limit(wire_client, options_fixture, search_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/search/courses/").mock(
        return_value=httpx.Response(200, json=search_fixture)
    )
    wire_client()
    out = await server.search_courses("CIS-1200", limit=1)
    assert out["count"] == len(search_fixture)
    assert len(out["results"]) <= 1


@pytest.mark.asyncio
@respx.mock
async def test_get_course_details_formats_meetings(wire_client, options_fixture, course_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/CIS-1200/").mock(
        return_value=httpx.Response(200, json=course_fixture)
    )
    wire_client()
    out = await server.get_course_details("CIS-1200")
    assert out["id"] == "CIS-1200"
    # meetings should be human-readable strings, not raw decimals
    first = out["sections"][0]
    assert all(isinstance(mt, str) for mt in first["meetings"])
    assert any(":" in mt for mt in first["meetings"])


@pytest.mark.asyncio
@respx.mock
async def test_get_course_not_found_returns_error(wire_client, options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/ZZZ-9999/").mock(return_value=httpx.Response(404))
    wire_client()
    out = await server.get_course_details("ZZZ-9999")
    assert "error" in out


@pytest.mark.asyncio
@respx.mock
async def test_reviews_degrade_without_cookie(wire_client, options_fixture, course_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/CIS-1200/").mock(
        return_value=httpx.Response(200, json=course_fixture)
    )
    wire_client(session_cookie=None)
    out = await server.get_course_reviews("CIS-1200")
    assert out["auth_status"] == "unauthenticated"
    assert "aggregate_ratings" in out


@pytest.mark.asyncio
@respx.mock
async def test_reviews_authenticated(wire_client):
    respx.get(f"{BASE}/api/review/course/CIS-1200").mock(
        return_value=httpx.Response(200, json={"code": "CIS-1200", "instructors": []})
    )
    wire_client(session_cookie="sessionid=good")
    out = await server.get_course_reviews("CIS-1200")
    assert out["auth_status"] == "authenticated"


@pytest.mark.asyncio
@respx.mock
async def test_check_schedule_conflicts(wire_client, options_fixture, course_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/CIS-1200/").mock(
        return_value=httpx.Response(200, json=course_fixture)
    )
    wire_client()
    # two lecture sections of the same course almost certainly clash or not;
    # at minimum the tool resolves them and returns a structured result.
    first_two = [s["id"] for s in course_fixture["sections"][:2]]
    out = await server.check_schedule_conflicts(first_two)
    assert "has_conflicts" in out
    assert out["not_found"] == []


@pytest.mark.asyncio
@respx.mock
async def test_build_schedule_reports_credits(wire_client, options_fixture, course_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/CIS-1200/").mock(
        return_value=httpx.Response(200, json=course_fixture)
    )
    wire_client()
    sid = course_fixture["sections"][0]["id"]
    out = await server.build_schedule([sid])
    assert "total_credits" in out
    assert "weekly_grid" in out


@pytest.mark.asyncio
@respx.mock
async def test_recommend_courses_sorts(wire_client, options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    payload = [
        {"id": "A", "course_quality": 2.0},
        {"id": "B", "course_quality": 3.5},
        {"id": "C", "course_quality": None},
    ]
    respx.get(f"{BASE}/api/base/{sem}/search/courses/").mock(
        return_value=httpx.Response(200, json=payload)
    )
    wire_client()
    out = await server.recommend_courses("anything", sort_by="course_quality")
    assert out["results"][0]["id"] == "B"  # highest quality first
    assert out["results"][-1]["id"] == "C"  # unrated last


# -- schedule writes -------------------------------------------------------
@pytest.mark.asyncio
@respx.mock
async def test_save_schedule_requires_auth(wire_client):
    wire_client(session_cookie=None)
    out = await server.save_schedule("My Plan", ["CIS-1200-001"])
    assert "error" in out
    assert "PENN_COURSES_SESSION_COOKIE" in out["hint"]


@pytest.mark.asyncio
@respx.mock
async def test_save_schedule_creates(wire_client, options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    route = respx.post(f"{BASE}/api/plan/schedules/").mock(
        return_value=httpx.Response(201, json={"message": "success", "id": 12345})
    )
    wire_client(session_cookie="sessionid=good; csrftoken=tok")
    out = await server.save_schedule("My Plan", ["cis-1200-001"])
    assert out["saved"] is True
    assert out["action"] == "created"
    assert out["schedule_id"] == 12345
    # CSRF token forwarded; section code normalized to upper-case in the payload
    req = route.calls.last.request
    assert req.headers.get("x-csrftoken") == "tok"
    assert b"CIS-1200-001" in req.content


@pytest.mark.asyncio
@respx.mock
async def test_save_schedule_updates_existing(wire_client, options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    route = respx.put(f"{BASE}/api/plan/schedules/999/").mock(
        return_value=httpx.Response(200, json={"id": 999})
    )
    wire_client(session_cookie="sessionid=good; csrftoken=tok")
    out = await server.save_schedule("Plan", ["CIS-1600-001"], schedule_id=999)
    assert out["action"] == "updated"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_list_schedules(wire_client):
    respx.get(f"{BASE}/api/plan/schedules/").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "S", "semester": "2026C", "sections": [{"id": "CIS-1200-001"}]}
            ],
        )
    )
    wire_client(session_cookie="sessionid=good; csrftoken=tok")
    out = await server.list_schedules()
    assert out["count"] == 1
    assert out["schedules"][0]["sections"] == ["CIS-1200-001"]


@pytest.mark.asyncio
@respx.mock
async def test_delete_schedule(wire_client):
    route = respx.delete(f"{BASE}/api/plan/schedules/77/").mock(return_value=httpx.Response(204))
    wire_client(session_cookie="sessionid=good; csrftoken=tok")
    out = await server.delete_schedule(77)
    assert out["deleted"] is True
    assert route.called
