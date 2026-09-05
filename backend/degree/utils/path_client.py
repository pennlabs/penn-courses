"""
A client for the degree endpoints Path@Penn exposes at courses.upenn.edu.

Path@Penn proxies DegreeWorks, and unlike the DegreeWorks server itself these endpoints need
no authentication: the audits they return are what-if runs against a dummy student record
(Stu_id="*", Stu_name="*Test"), so they describe the degree template and contain no student
data. That means no token scraping, unlike `degreeworks_client.DegreeworksClient`.

The `programs-v2-*` routes use the same POST convention as the course search Path@Penn's own
front end uses (see `courses.management.commands.sync_path_status`): the body is the payload
JSON, URL-encoded, and the route goes in the query string.
"""

import json
import re
import time
from urllib.parse import quote

import requests


BASE_URL = "https://courses.upenn.edu/api/"

# Path@Penn serves these routes to its own front end, so send what a browser would.
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://courses.upenn.edu",
    "referer": "https://courses.upenn.edu/",
    "x-requested-with": "XMLHttpRequest",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Degree codes we model in `degree.models.program_choices`. Path lists graduate programs,
# minors and certificates from the same catalog, which we skip.
UNDERGRADUATE_DEGREE_CODES = {"BA", "BAS", "BS", "BSE", "BSN"}

# Minors use this in place of a degree code, e.g. MATH-MINOR.
MINOR_DEGREE_CODE = "MINOR"


class PathError(Exception):
    """Raised when Path@Penn returns an error instead of the payload we asked for."""


class PathClient:
    """
    Fetches the program catalog and degree audits from Path@Penn.

    `delay` is the number of seconds to wait between requests. A full scrape is one request
    per program per catalog year, so be polite by default.
    """

    def __init__(self, session=None, timeout=30, delay=0.5):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.delay = delay
        self._last_request_at = None

    def _wait(self):
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_at = time.monotonic()

    def _call(self, route: str, payload: dict) -> dict | list:
        """
        Calls one of the `page=fose` routes. The body is the payload JSON, URL-encoded, which
        is what Path's own `fose.serverAPI.call` sends.
        """
        self._wait()
        res = self.session.post(
            BASE_URL,
            params={"page": "fose", "route": route},
            data=quote(json.dumps(payload)),
            timeout=self.timeout,
        )
        res.raise_for_status()
        body = res.json()
        if isinstance(body, dict) and body.get("error"):
            raise PathError(f"{route} {payload}: {body['error']}")
        return body

    def list_programs(self, srcdb: str) -> list[dict]:
        """
        Returns every program in the catalog for the given term, as dicts of `code` and
        `title`. Codes look like MAJR-DEGC or MAJR-DEGC-CONC, e.g. CMPE-BSE, ANTH-BA-ARC.
        """
        return self._call("programs-v2-list", {"srcdb": srcdb, "programsType": ""})

    def undergraduate_programs(self, srcdb: str) -> list[dict]:
        """
        Returns the subset of `list_programs` whose degree code is one we model.
        """
        return [
            program
            for program in self.list_programs(srcdb)
            if split_program_code(program["code"])[1] in UNDERGRADUATE_DEGREE_CODES
        ]

    def minor_programs(self, srcdb: str) -> list[dict]:
        """
        Returns the minors in the catalog, whose codes look like MATH-MINOR.

        Note that a minor's `programs-v2-info` has an empty `sis_prog_code`, and puts the
        minor's code in `majr_code` rather than `minr_code`.
        """
        return [
            program
            for program in self.list_programs(srcdb)
            if split_program_code(program["code"])[1] == MINOR_DEGREE_CODE
        ]

    def program_info(self, program_code: str, srcdb: str) -> dict:
        """
        Returns a program's metadata, including `sis_prog_code` (the program code we store on
        `Degree.program`, e.g. EU_BSE) and `audit_xml` (the DegreeWorks audit).
        """
        info = self._call("programs-v2-info", {"srcdb": srcdb, "programCode": program_code})
        if not info.get("audit_xml"):
            raise PathError(f"No audit_xml for {program_code} at srcdb {srcdb}")
        return info


def split_program_code(program_code: str) -> tuple[str, str, str | None]:
    """
    Splits a Path program code into its major, degree and concentration codes. Returns the
    concentration as None when the code has no concentration segment.

    Note that NCON ("No Concentration") is left as-is rather than folded into None: Path lists
    both `CMPE-BSE` and `CMPE-BSE-NCON` for two programs, so they are not interchangeable.
    """
    parts = program_code.split("-")
    if len(parts) == 2:
        return parts[0], parts[1], None
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    raise ValueError(f"Unexpected program code format: {program_code}")


def split_program_title(title: str, degree_code: str) -> tuple[str, str | None]:
    """
    Splits a Path program title into the major name and the concentration name, which
    `Degree.major_name` and `Degree.concentration_name` currently have no source for.

    Titles read like "Computer Engineering BSE", "Anthropology BA (Archaeology)" or
    "Biomedical Science BA (Biomedical Devices) - College 2nd Major ONLY": the concentration
    is parenthesized but not necessarily at the end, and the major name is whatever precedes
    the degree code.
    """
    concentration_name = None
    match = re.search(r"\(([^)]*)\)", title)
    if match:
        concentration_name = match.group(1).strip() or None
        title = title.replace(match.group(0), "", 1)

    match = re.match(rf"^(.*?)\s+{re.escape(degree_code)}\b", title)
    major_name = match.group(1) if match else title
    return major_name.strip(), concentration_name
