import csv
import json
import random
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.db.models import Min, Q

from courses.models import Course
from courses.util import get_semesters


API_URL = "https://courses.upenn.edu/api/?page=fose&route=details"
DEFAULT_OUTPUT_DIR = Path("courses/data/prereq_scrapes")


def extract_clssnotes(payload):
    values = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "clssnotes":
                    values.append(value)
                walk(value)
        elif isinstance(node, list):
            for item in node: 
                walk(item)

    walk(payload)

    if not values:
        return None

    unique_values = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)

    if len(unique_values) == 1:
        return unique_values[0]
    return unique_values


def normalize_course_code(course_code: str) -> str:
    """
    Normalize course code for upstream API group field.
    Examples:
      - CIS-1210 -> CIS 1210
      - cis 1210 -> CIS 1210
    """
    code = course_code.strip().upper().replace("-", " ")
    code = re.sub(r"\s+", " ", code)
    return code


def parse_pair_string(pair: str) -> tuple[str, str]:
    """
    Parse a pair argument string of the form:
      - "CIS 1210:14309"
      - "CIS-1210,14309"
      - "CIS 1210 14309"
    """
    pair = pair.strip()
    if ":" in pair:
        left, right = pair.split(":", 1)
    elif "," in pair:
        left, right = pair.split(",", 1)
    else:
        parts = pair.rsplit(" ", 1)
        if len(parts) != 2:
            raise ValueError(f"Could not parse pair '{pair}'.")
        left, right = parts[0], parts[1]

    course_code = normalize_course_code(left)
    crn = right.strip()
    if not course_code or not crn:
        raise ValueError(f"Missing code or CRN in pair '{pair}'.")
    return course_code, crn


def load_pairs_from_file(file_path: Path) -> list[tuple[str, str]]:
    """
    Load (course_code, crn) pairs from json/csv.

    JSON formats supported:
      1) [{"code": "CIS 1210", "crn": "14309"}, ...]
      2) [["CIS 1210", "14309"], ...]

    CSV format supported:
      Headers must include: code, crn
    """
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(file_path.read_text())
        pairs: list[tuple[str, str]] = []
        for row in data:
            if isinstance(row, dict):
                code = row.get("code")
                crn = row.get("crn")
            else:
                code, crn = row
            if not code or not crn:
                continue
            pairs.append((normalize_course_code(str(code)), str(crn).strip()))
        return pairs

    if suffix == ".csv":
        pairs = []
        with file_path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or "code" not in reader.fieldnames or "crn" not in reader.fieldnames:
                raise ValueError("CSV must include 'code' and 'crn' headers.")
            for row in reader:
                code = row.get("code")
                crn = row.get("crn")
                if not code or not crn:
                    continue
                pairs.append((normalize_course_code(code), crn.strip()))
        return pairs

    raise ValueError("Unsupported --input-file type. Use .json or .csv")


def load_pairs_from_courses(semesters: list[str]) -> list[tuple[str, str]]:
    queryset = (
        Course.objects.filter(semester__in=semesters)
        .annotate(
            sample_crn=Min(
                "sections__crn",
                filter=Q(sections__crn__isnull=False) & ~Q(sections__crn=""),
            )
        )
        .exclude(sample_crn__isnull=True)
        .values_list("department__code", "code", "sample_crn")
        .order_by("department__code", "code")
    )

    return [(normalize_course_code(f"{dept} {code}"), str(crn)) for dept, code, crn in queryset]


class Command(BaseCommand):
    help = "Scrape clssnotes from courses.upenn.edu and save compact JSON output."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pair",
            action="append",
            default=[],
            help=(
                "Course/CRN pair. Repeat this flag for multiple pairs. "
                "Examples: --pair 'CIS 1210:14309' or --pair 'CIS-1200,14308'"
            ),
        )
        parser.add_argument(
            "--input-file",
            type=str,
            default=None,
            help="Path to .json or .csv containing course code + CRN pairs.",
        )
        parser.add_argument(
            "--all-course-codes",
            action="store_true",
            default=False,
            help="Scrape one CRN per course code from DB instead of manually provided pairs.",
        )
        parser.add_argument(
            "--semesters",
            type=str,
            default=None,
            help=(
                "Semester scope for --all-course-codes. "
                "Comma-separated (e.g. 2025C,2026A), 'all', or omitted for current semester."
            ),
        )
        parser.add_argument(
            "--output-file",
            type=str,
            default=None,
            help="Optional explicit output path. Defaults to timestamped file in courses/data/prereq_scrapes.",
        )
        parser.add_argument(
            "--timeout-seconds",
            type=int,
            default=20,
            help="HTTP timeout in seconds (default: 20).",
        )
        parser.add_argument(
            "--sleep-seconds",
            type=float,
            default=0.0,
            help="Base delay between requests in seconds (default: 0).",
        )
        parser.add_argument(
            "--jitter-seconds",
            type=float,
            default=0.0,
            help="Random extra delay per request in seconds, uniformly sampled from [0, jitter].",
        )
        parser.add_argument(
            "--max-requests",
            type=int,
            default=None,
            help="Optional cap on total requests sent after deduplication.",
        )

    def handle(self, *args, **kwargs):
        pair_args: list[str] = kwargs["pair"]
        input_file = kwargs["input_file"]
        all_course_codes = kwargs["all_course_codes"]
        timeout_seconds = kwargs["timeout_seconds"]
        sleep_seconds = kwargs["sleep_seconds"]
        jitter_seconds = kwargs["jitter_seconds"]
        max_requests = kwargs["max_requests"]

        if sleep_seconds < 0:
            raise ValueError("--sleep-seconds must be >= 0")
        if jitter_seconds < 0:
            raise ValueError("--jitter-seconds must be >= 0")
        if max_requests is not None and max_requests <= 0:
            raise ValueError("--max-requests must be > 0")

        pairs: list[tuple[str, str]] = []

        for pair in pair_args:
            pairs.append(parse_pair_string(pair))

        if input_file:
            pairs.extend(load_pairs_from_file(Path(input_file)))

        if all_course_codes:
            semesters = get_semesters(kwargs.get("semesters"))
            db_pairs = load_pairs_from_courses(semesters)
            self.stdout.write(
                f"Loaded {len(db_pairs)} course/CRN pairs from DB for semesters: {', '.join(semesters)}"
            )
            pairs.extend(db_pairs)

        deduped_pairs = []
        seen = set()
        for course_code, crn in pairs:
            key = (course_code, crn)
            if key not in seen:
                deduped_pairs.append(key)
                seen.add(key)

        if max_requests is not None:
            deduped_pairs = deduped_pairs[:max_requests]

        if not deduped_pairs:
            raise ValueError(
                "No pairs provided. Use one or more --pair values and/or --input-file."
            )

        if kwargs["output_file"]:
            output_path = Path(kwargs["output_file"])
        else:
            now = datetime.now(UTC)
            output_path = DEFAULT_OUTPUT_DIR / f"prereq_scrape_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
            }
        )

        records = []
        total_requests = len(deduped_pairs)
        if sleep_seconds > 0 or jitter_seconds > 0:
            self.stdout.write(
                f"Throttling enabled: base sleep {sleep_seconds:.3f}s, jitter up to {jitter_seconds:.3f}s"
            )

        for index, (course_code, crn) in enumerate(deduped_pairs, start=1):
            payload = {
                "group": f"code:{course_code}",
                "key": f"crn:{crn}",
            }
            self.stdout.write(f"[{index}/{total_requests}] Fetching {course_code} (CRN {crn})")

            record = {
                "course_code": course_code,
                "crn": crn,
                "clssnotes": None,
            }

            try:
                response = session.post(API_URL, json=payload, timeout=timeout_seconds)
                try:
                    response_json = response.json()
                    record["clssnotes"] = extract_clssnotes(response_json)
                except ValueError:
                    record["clssnotes"] = None
            except requests.RequestException as exc:
                self.stderr.write(
                    self.style.WARNING(
                        f"Request failed for {course_code} (CRN {crn}): {exc}"
                    )
                )

            records.append(record)

            if index < total_requests and (sleep_seconds > 0 or jitter_seconds > 0):
                delay = sleep_seconds + (random.uniform(0.0, jitter_seconds) if jitter_seconds > 0 else 0.0)
                time.sleep(delay)

        output_path.write_text(json.dumps(records, indent=2, sort_keys=True))

        with_notes = sum(1 for record in records if record.get("clssnotes"))
        without_notes = len(records) - with_notes
        self.stdout.write(self.style.SUCCESS(f"Saved output to {output_path}"))
        self.stdout.write(
            f"Requests: {len(records)} | With clssnotes: {with_notes} | Without clssnotes: {without_notes}"
        )