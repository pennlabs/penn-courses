import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course, Section
from courses.util import get_semesters


SCRAPE_OUTPUT_DIR = Path("courses/data/prereq_scrapes")
COURSE_TOKEN_RE = re.compile(r"([A-Za-z]{2,4})\s*-?\s*(\d{3,4}[A-Za-z]?)|(\d{3,4}[A-Za-z]?)")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def parse_prereq_pairs(prereq_text: str) -> set[tuple[str, str]]:
	if not prereq_text:
		return set()

	clean_text = HTML_TAG_RE.sub(" ", prereq_text).upper()
	pairs = set()
	last_dept = None
	for match in COURSE_TOKEN_RE.finditer(clean_text):
		dept = match.group(1)
		code = match.group(2) or match.group(3)

		if dept:
			last_dept = dept
			pairs.add((dept, code))
			continue

		if last_dept:
			pairs.add((last_dept, code))

	return pairs


def resolve_prereq_course(dept_code: str, course_code: str, semester: str) -> Course | None:
	same_semester = Course.objects.filter(
		department__code=dept_code,
		code=course_code,
		semester=semester,
	).first()
	if same_semester:
		return same_semester.primary_listing

	previous = (
		Course.objects.filter(
			department__code=dept_code,
			code=course_code,
			semester__lt=semester,
		)
		.order_by("-semester")
		.first()
	)
	if previous:
		return previous.primary_listing

	fallback = (
		Course.objects.filter(
			department__code=dept_code,
			code=course_code,
		)
		.order_by("-semester")
		.first()
	)
	return fallback.primary_listing if fallback else None


def get_latest_scrape_file() -> Path:
	candidates = sorted(SCRAPE_OUTPUT_DIR.glob("prereq_scrape_*.json"))
	if not candidates:
		raise ValueError(
			f"No scrape output files found in {SCRAPE_OUTPUT_DIR}. Run scrape_prereqs first."
		)
	return candidates[-1]


def load_scrape_records(scrape_file: Path) -> list[dict]:
	payload = json.loads(scrape_file.read_text())
	if isinstance(payload, list):
		return payload
	if isinstance(payload, dict) and isinstance(payload.get("results"), list):
		return payload["results"]
	raise ValueError("Unsupported scrape JSON format.")


def parse_course_code(course_code: str) -> tuple[str, str]:
	parts = course_code.strip().upper().replace("-", " ").split()
	if len(parts) < 2:
		raise ValueError(f"Could not parse course_code '{course_code}'.")
	return parts[0], parts[1]


def get_notes_text(clssnotes) -> str:
	if isinstance(clssnotes, list):
		return "\n".join(note for note in clssnotes if isinstance(note, str))
	if isinstance(clssnotes, str):
		return clssnotes
	return ""


def populate_prereqs_from_scrape(
	semesters: list[str],
	records: list[dict],
	dry_run: bool = False,
	clear_existing: bool = False,
	verbose: bool = False,
):
	parsed_pairs = 0
	created_links = 0
	unresolved_pairs = 0
	missing_courses = 0
	courses_touched = 0

	with transaction.atomic():
		for record in tqdm(records, disable=not verbose):
			course_code = record.get("course_code")
			crn = record.get("crn")
			notes_text = get_notes_text(record.get("clssnotes"))

			if not course_code or not crn:
				continue

			try:
				dept_code, class_code = parse_course_code(str(course_code))
			except ValueError:
				missing_courses += 1
				continue

			section = (
				Section.objects.filter(
					crn=str(crn),
					course__semester__in=semesters,
					course__department__code=dept_code,
					course__code=class_code,
				)
				.select_related("course__primary_listing")
				.first()
			)
			if section is None:
				missing_courses += 1
				continue

			course = section.course.primary_listing
			courses_touched += 1

			pairs = parse_prereq_pairs(notes_text)
			parsed_pairs += len(pairs)

			resolved_prereqs = []
			for prereq_dept, prereq_code in pairs:
				prereq = resolve_prereq_course(prereq_dept, prereq_code, course.semester)
				if prereq is None:
					unresolved_pairs += 1
					continue
				if prereq.id == course.id:
					continue
				resolved_prereqs.append(prereq)

			if dry_run:
				created_links += len(resolved_prereqs)
				continue

			if clear_existing:
				course.prerequisite_courses.set(resolved_prereqs)
			elif resolved_prereqs:
				course.prerequisite_courses.add(*resolved_prereqs)

			created_links += len(resolved_prereqs)

		if dry_run:
			transaction.set_rollback(True)

	return {
		"records": len(records),
		"courses_touched": courses_touched,
		"parsed_pairs": parsed_pairs,
		"created_links": created_links,
		"unresolved_pairs": unresolved_pairs,
		"missing_courses": missing_courses,
	}


class Command(BaseCommand):
	help = "Populate structured prerequisite relationships from scrape_prereqs JSON output."

	def add_arguments(self, parser):
		parser.add_argument(
			"--semesters",
			type=str,
			default=None,
			help=(
				"Comma-separated semesters (e.g. 2024C,2025A), 'all', or omitted for current semester."
			),
		)
		parser.add_argument(
			"--scrape-file",
			type=str,
			default=None,
			help="Path to scrape_prereqs JSON output. Defaults to latest file in courses/data/prereq_scrapes.",
		)
		parser.add_argument(
			"--dry-run",
			action="store_true",
			default=False,
			help="Parse and resolve prerequisites without writing DB changes.",
		)
		parser.add_argument(
			"--clear-existing",
			action="store_true",
			default=False,
			help="Clear existing links before writing recomputed prerequisite links.",
		)

	def handle(self, *args, **kwargs):
		semesters = get_semesters(kwargs.get("semesters"))
		dry_run = kwargs.get("dry_run", False)
		clear_existing = kwargs.get("clear_existing", False)

		if kwargs.get("scrape_file"):
			scrape_file = Path(kwargs["scrape_file"])
		else:
			scrape_file = get_latest_scrape_file()

		if not scrape_file.exists():
			raise ValueError(f"Scrape file not found: {scrape_file}")

		records = load_scrape_records(scrape_file)

		if clear_existing and not dry_run:
			confirm = input(
				"This will modify prerequisite links and clear existing links for matched courses. Continue? (y/N): "
			)
			if confirm.lower() != "y":
				self.stdout.write("Operation cancelled by user.")
				return 1

		self.stdout.write(f"Using scrape file: {scrape_file}")
		self.stdout.write(
			f"Populating prerequisite relationships for semesters: {', '.join(semesters)}"
		)

		stats = populate_prereqs_from_scrape(
			semesters=semesters,
			records=records,
			dry_run=dry_run,
			clear_existing=clear_existing,
			verbose=True,
		)

		self.stdout.write(self.style.SUCCESS("Finished populate_prereqs."))
		self.stdout.write(f"Records scanned: {stats['records']}")
		self.stdout.write(f"Courses matched by CRN: {stats['courses_touched']}")
		self.stdout.write(f"Prereq pairs parsed: {stats['parsed_pairs']}")
		self.stdout.write(f"Links created/resolved: {stats['created_links']}")
		self.stdout.write(f"Unresolved pairs: {stats['unresolved_pairs']}")
		self.stdout.write(f"Missing course matches: {stats['missing_courses']}")
