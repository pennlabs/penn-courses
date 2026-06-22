import httpx
import pytest
import respx

from penn_course_mcp.client import PennCoursesClient
from penn_course_mcp.config import Settings
from penn_course_mcp.errors import CourseNotFound, ReviewAuthRequired


BASE = "https://penncoursereview.com"


def make_client(**overrides) -> PennCoursesClient:
    settings = Settings(base_url=BASE, semester="current", cache_ttl=3600, **overrides)
    return PennCoursesClient(settings)


@pytest.mark.asyncio
@respx.mock
async def test_resolve_semester_from_options(options_fixture):
    route = respx.get(f"{BASE}/api/options/").mock(
        return_value=httpx.Response(200, json=options_fixture)
    )
    client = make_client()
    sem = await client.resolve_semester("current")
    assert sem == options_fixture["SEMESTER"]
    # second resolution is cached -> no second request
    await client.resolve_semester(None)
    assert route.call_count == 1
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_resolve_semester_passthrough():
    client = make_client()
    assert await client.resolve_semester("2025A") == "2025A"
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_get_course_caches(options_fixture, course_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    route = respx.get(f"{BASE}/api/base/{sem}/courses/CIS-1200/").mock(
        return_value=httpx.Response(200, json=course_fixture)
    )
    client = make_client()
    a = await client.get_course("current", "CIS-1200")
    b = await client.get_course(None, "cis-1200")  # lowercased + cached
    assert a["id"] == b["id"] == "CIS-1200"
    assert route.call_count == 1
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_get_course_not_found(options_fixture):
    respx.get(f"{BASE}/api/options/").mock(return_value=httpx.Response(200, json=options_fixture))
    sem = options_fixture["SEMESTER"]
    respx.get(f"{BASE}/api/base/{sem}/courses/ZZZ-9999/").mock(return_value=httpx.Response(404))
    client = make_client()
    with pytest.raises(CourseNotFound):
        await client.get_course("current", "ZZZ-9999")
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_get_review_requires_cookie():
    client = make_client()  # no session cookie
    with pytest.raises(ReviewAuthRequired):
        await client.get_review("CIS-1200")
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_get_review_403_maps_to_auth_required():
    respx.get(f"{BASE}/api/review/course/CIS-1200").mock(return_value=httpx.Response(403))
    client = make_client(session_cookie="sessionid=bad")
    with pytest.raises(ReviewAuthRequired):
        await client.get_review("CIS-1200")
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_get_review_success():
    respx.get(f"{BASE}/api/review/course/CIS-1200").mock(
        return_value=httpx.Response(200, json={"code": "CIS-1200", "reviews": []})
    )
    client = make_client(session_cookie="sessionid=good")
    data = await client.get_review("CIS-1200")
    assert data["code"] == "CIS-1200"
    await client.aclose()
