"""Runtime configuration, sourced from environment variables.

Everything is optional: with zero configuration the server talks to the public
Penn Courses API. Setting ``PENN_COURSES_SESSION_COOKIE`` additionally unlocks
the authenticated review endpoints.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import __version__


DEFAULT_BASE_URL = "https://penncoursereview.com"
DEFAULT_SEMESTER = "current"
DEFAULT_CACHE_TTL = 3600
DEFAULT_TIMEOUT = 20.0


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    base_url: str = DEFAULT_BASE_URL
    semester: str = DEFAULT_SEMESTER
    cache_ttl: int = DEFAULT_CACHE_TTL
    timeout: float = DEFAULT_TIMEOUT
    user_agent: str = f"penn-course-mcp/{__version__}"
    session_cookie: str | None = None

    @property
    def reviews_enabled(self) -> bool:
        return bool(self.session_cookie)

    @classmethod
    def from_env(cls) -> "Settings":
        cookie = os.environ.get("PENN_COURSES_SESSION_COOKIE") or None
        return cls(
            base_url=os.environ.get("PENN_COURSES_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            semester=os.environ.get("PENN_COURSES_SEMESTER", DEFAULT_SEMESTER),
            cache_ttl=_get_int("PENN_COURSES_CACHE_TTL", DEFAULT_CACHE_TTL),
            timeout=_get_float("PENN_COURSES_TIMEOUT", DEFAULT_TIMEOUT),
            user_agent=os.environ.get("PENN_COURSES_USER_AGENT", f"penn-course-mcp/{__version__}"),
            session_cookie=cookie,
        )
