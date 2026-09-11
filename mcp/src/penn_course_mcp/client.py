"""Async HTTP client for the Penn Courses public API.

Wraps the handful of upstream endpoints with caching, semester resolution,
politeness controls, and translation of HTTP errors into domain exceptions.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
from cachetools import TTLCache

from .config import Settings
from .errors import CourseNotFound, ReviewAuthRequired, UpstreamError, WriteAuthRequired


# Search results change a bit more often than catalog/detail data, so cache them
# for a shorter window.
SEARCH_CACHE_TTL = 300
MAX_CONCURRENCY = 5


class PennCoursesClient:
    """Thin async wrapper over the Penn Courses REST API."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self._client: httpx.AsyncClient | None = None
        self._sem = asyncio.Semaphore(MAX_CONCURRENCY)
        # Long-lived cache for stable endpoints (catalog, course detail, options).
        self._cache: TTLCache = TTLCache(maxsize=2048, ttl=self.settings.cache_ttl)
        # Short-lived cache for searches.
        self._search_cache: TTLCache = TTLCache(maxsize=512, ttl=SEARCH_CACHE_TTL)
        self._resolved_semester: str | None = None

    # -- lifecycle ---------------------------------------------------------
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.settings.base_url,
                headers={
                    "User-Agent": self.settings.user_agent,
                    "Accept": "application/json",
                },
                timeout=self.settings.timeout,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -- low-level GET -----------------------------------------------------
    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        cache: TTLCache | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        cache_key = path + ("?" + httpx.QueryParams(params).__str__() if params else "")
        store = cache if cache is not None else self._cache
        if cache_key in store:
            return store[cache_key]

        async with self._sem:
            data = await self._request_with_retry(path, params=params, headers=headers)
        store[cache_key] = data
        return data

    async def _request_with_retry(
        self,
        path: str,
        *,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        last_exc: Exception | None = None
        for attempt in range(2):  # one retry on transient failures
            try:
                resp = await self.client.get(path, params=params, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise UpstreamError(f"Request to {path} failed: {exc}") from exc

            if resp.status_code == 404:
                raise CourseNotFound(path)
            if resp.status_code in (401, 403):
                raise UpstreamError(
                    f"Access denied ({resp.status_code}) for {path}.",
                    status=resp.status_code,
                )
            if resp.status_code >= 500:
                last_exc = UpstreamError(
                    f"Upstream error {resp.status_code} for {path}.",
                    status=resp.status_code,
                )
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise last_exc
            try:
                return resp.json()
            except ValueError as exc:
                raise UpstreamError(f"Invalid JSON from {path}: {exc}") from exc
        # unreachable, but satisfies type checkers
        raise UpstreamError(f"Request to {path} failed: {last_exc}")

    # -- endpoints ---------------------------------------------------------
    async def get_options(self) -> dict[str, Any]:
        return await self._get_json("/api/options/")

    async def resolve_semester(self, semester: str | None) -> str:
        """Resolve ``None``/``"current"`` to a concrete semester code (e.g. 2026C)."""
        candidate = semester or self.settings.semester
        if candidate and candidate.lower() != "current":
            return candidate
        if self._resolved_semester is None:
            options = await self.get_options()
            self._resolved_semester = options.get("SEMESTER", "current")
        return self._resolved_semester

    async def search_courses(self, semester: str | None, query: str) -> list[dict[str, Any]]:
        sem = await self.resolve_semester(semester)
        return await self._get_json(
            f"/api/base/{sem}/search/courses/",
            params={"search": query},
            cache=self._search_cache,
        )

    async def list_all_courses(self, semester: str | None) -> list[dict[str, Any]]:
        sem = await self.resolve_semester(semester)
        return await self._get_json(f"/api/base/{sem}/courses/")

    async def get_course(self, semester: str | None, code: str) -> dict[str, Any]:
        sem = await self.resolve_semester(semester)
        code = code.upper()
        try:
            return await self._get_json(f"/api/base/{sem}/courses/{code}/")
        except CourseNotFound as exc:
            raise CourseNotFound(code, sem) from exc

    # -- authenticated writes (Penn Course Plan schedules) -----------------
    def _csrf_token(self) -> str | None:
        """Pull the csrftoken out of the configured session cookie, if present."""
        match = re.search(r"csrftoken=([^;]+)", self.settings.session_cookie or "")
        return match.group(1) if match else None

    async def _authed_request(self, method: str, path: str, *, json_body: Any | None = None) -> Any:
        """Make an authenticated request (used for the Plan schedule endpoints).

        Unsafe methods carry the CSRF token plus matching Referer/Origin so Django's
        SessionAuthentication accepts them. Never cached.
        """
        if not self.settings.session_cookie:
            raise WriteAuthRequired()
        headers = {
            "Cookie": self.settings.session_cookie,
            "Accept": "application/json",
            "Referer": self.settings.base_url + "/",
            "Origin": self.settings.base_url,
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        token = self._csrf_token()
        if token:
            headers["X-CSRFToken"] = token

        async with self._sem:
            try:
                resp = await self.client.request(method, path, json=json_body, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                raise UpstreamError(f"{method} {path} failed: {exc}") from exc

        if resp.status_code in (401, 403):
            raise WriteAuthRequired()
        if resp.status_code == 404:
            raise CourseNotFound(path)
        if resp.status_code >= 400:
            raise UpstreamError(
                f"{method} {path} failed ({resp.status_code}): {resp.text[:200]}",
                status=resp.status_code,
            )
        if resp.status_code == 204 or not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}

    async def list_schedules(self) -> list[dict[str, Any]]:
        """Return the authenticated user's saved Penn Course Plan schedules."""
        return await self._authed_request("GET", "/api/plan/schedules/")

    async def save_schedule(
        self,
        *,
        name: str,
        semester: str | None,
        section_ids: list[str],
        schedule_id: int | None = None,
    ) -> dict[str, Any]:
        """Create (or update, if ``schedule_id`` is given) a Plan schedule.

        ``section_ids`` are full section codes like 'CIS-1200-001'.
        """
        if not self.settings.session_cookie:
            raise WriteAuthRequired()
        sem = await self.resolve_semester(semester)
        payload: dict[str, Any] = {
            "semester": sem,
            "name": name,
            "sections": [{"id": s.upper(), "semester": sem} for s in section_ids],
        }
        if schedule_id is not None:
            payload["id"] = schedule_id
            return await self._authed_request(
                "PUT", f"/api/plan/schedules/{schedule_id}/", json_body=payload
            )
        return await self._authed_request("POST", "/api/plan/schedules/", json_body=payload)

    async def delete_schedule(self, schedule_id: int) -> None:
        """Delete a saved schedule by id."""
        await self._authed_request("DELETE", f"/api/plan/schedules/{schedule_id}/")

    async def get_review(self, code: str) -> dict[str, Any]:
        """Fetch detailed reviews. Requires an authenticated session cookie."""
        code = code.upper()
        if not self.settings.session_cookie:
            raise ReviewAuthRequired(code)
        headers = {"Cookie": self.settings.session_cookie}
        try:
            return await self._get_json(f"/api/review/course/{code}", headers=headers)
        except UpstreamError as exc:
            if exc.status in (401, 403):
                raise ReviewAuthRequired(code) from exc
            raise
        except CourseNotFound as exc:
            raise CourseNotFound(code) from exc
