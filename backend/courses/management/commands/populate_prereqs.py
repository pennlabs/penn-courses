import re

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course
from courses.util import get_semesters


COURSE_TOKEN_RE = re.compile(r"([A-Za-z]{2,4})\s*-?\s*(\d{3,4}[A-Za-z]?)|(\d{3,4}[A-Za-z]?)")


def parse_prereq_pairs(prereq_text: str) -> set[tuple[str, str]]:
	"""
	Best-effort parser for prerequisites text, returning {(dept_code, course_code), ...}.

	Supports formats like:
	  - "CIS 1200"
	  - "CIS-1200"
	  - "CIS 1200, 1210"
	  - "MATH 1040 or CIS 1600"
	"""
	if not prereq_text:
		return set()

	pairs = set()
	last_dept = None
	for match in COURSE_TOKEN_RE.finditer(prereq_text.upper()):
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
	"""
	Resolve a parsed prerequisite course reference to a Course row.

	Preference order:
	  1) Same semester as the dependent course
	  2) Most recent earlier semester
	  3) Most recent available semester overall
	"""
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


def populate_prereqs(
	semesters: list[str],
	dry_run=False,
	clear_existing=False,
	verbose=False,
):
	courses = list(Course.objects.filter(semester__in=semesters).select_related("primary_listing"))

	parsed_pairs = 0
	created_links = 0
	unresolved_pairs = 0

	with transaction.atomic():
		for course in tqdm(courses, disable=not verbose):
			if clear_existing and not dry_run:
				course.prerequisite_courses.clear()

			pairs = parse_prereq_pairs(course.prerequisites)
			parsed_pairs += len(pairs)

			if not pairs:
				continue

			resolved_prereqs = []
			for dept_code, course_code in pairs:
				prereq = resolve_prereq_course(dept_code, course_code, course.semester)
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
				created_links += len(resolved_prereqs)
			else:
				if resolved_prereqs:
					course.prerequisite_courses.add(*resolved_prereqs)
					created_links += len(resolved_prereqs)

		if dry_run:
			transaction.set_rollback(True)

	return {
		"courses": len(courses),
		"parsed_pairs": parsed_pairs,
		"created_links": created_links,
		"unresolved_pairs": unresolved_pairs,
	}


class Command(BaseCommand):
	help = "Populate structured course prerequisite relationships from Course.prerequisites text."

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

		if clear_existing and not dry_run:
			confirm = input(
				"This will modify prerequisite links and clear existing links for selected courses. Continue? (y/N): "
			)
			if confirm.lower() != "y":
				self.stdout.write("Operation cancelled by user.")
				return 1

		self.stdout.write(
			f"Populating prerequisite relationships for semesters: {', '.join(semesters)}"
		)
		stats = populate_prereqs(
			semesters=semesters,
			dry_run=dry_run,
			clear_existing=clear_existing,
			verbose=True,
		)

		self.stdout.write(self.style.SUCCESS("Finished populate_prereqs."))
		self.stdout.write(f"Courses scanned: {stats['courses']}")
		self.stdout.write(f"Prereq pairs parsed: {stats['parsed_pairs']}")
		self.stdout.write(f"Links created/resolved: {stats['created_links']}")
		self.stdout.write(f"Unresolved pairs: {stats['unresolved_pairs']}")
