from textwrap import dedent

from botocore.exceptions import NoCredentialsError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Max, OuterRef, Subquery, Value
from tqdm import tqdm

from courses.management.commands.load_crosswalk import load_crosswalk
from courses.models import Course
from courses.util import get_semesters, in_dev


def recompute_parent_courses(
    semesters: list[str],
    overwrite_manual_changes=False,
    skip_xwalk=False,
    verbose=False,
):
    """
    Attemps to recompute empty `parent_course` fields for all courses in the specified semesters.

    :param semesters: Semesters for which you want to recompute `parent_course` fields.
    :param overwrite_manual_changes: CAUTION: If True, this script will overwrite any manual changes
        made to the `parent_course` fields of courses in this semester.
    :param skip_xwalk: If True, this script will skip loading crosswalk from s3 (e.g. for testing).
    :param verbose: Whether to print status/progress updates.
    """
    if verbose:
        print(
            f"Attempting to recompute empty `parent_course` fields for semesters {semesters}."
        )
    filled_links = 0
    for i, semester in enumerate(sorted(semesters)):
        if verbose:
            print(f"Processing semester {semester} ({i+1}/{len(semesters)})...")
        with transaction.atomic():
            courses = list(Course.objects.filter(semester=semester))
            full_codes = {course.full_code for course in courses}
            parent_candidates = (
                Course.objects.filter(
                    # TODO: we can include more parent candidates (e.g. with an extra 0
                    # appended or prepended to the course code) if we are careful about
                    # not blowing up topic size. Let's stay on the cautious size for now.
                    full_code__in=full_codes,
                    semester__lt=semester,
                )
                .annotate(
                    max_semester=Subquery(
                        Course.objects.filter(
                            full_code=OuterRef("full_code"),
                            semester__lt=semester,
                        )
                        .annotate(common=Value(1))
                        .values("common")
                        .annotate(max_semester=Max("semester"))
                        .values("max_semester")
                    )
                )
                .filter(semester=F("max_semester"))
            )
            parent_candidates = {p.full_code: p for p in parent_candidates}
            to_update = []
            for course in tqdm(courses, disable=not verbose):
                if course.manually_set_parent_course and not overwrite_manual_changes:
                    continue
                # TODO: do we want to apply any additional filters/checks before deciding to link
                # a course to its parent candidate (most recent course with same full code)?
                parent = parent_candidates.get(course.full_code)
                if course.parent_course != parent or course.manually_set_parent_course:
                    course.manually_set_parent_course = False
                    course.parent_course = parent
                    to_update.append(course)
            Course.objects.bulk_update(
                to_update,
                ["parent_course", "manually_set_parent_course"],
                batch_size=4000,
            )
            if verbose:
                print(f"Recomputed {len(to_update)} `parent_course` links.")
            filled_links += len(to_update)
    if verbose:
        print(
            f"Finished recomputing {filled_links} `parent_course` fields for semesters {semesters}."
        )

    try:
        if not skip_xwalk:
            load_crosswalk(print_missing=False, verbose=verbose)
    except NoCredentialsError as e:
        if not in_dev():
            raise e
        print("NOTE: load_crosswalk skipped due to missing AWS credentials.")


class Command(BaseCommand):
    help = "This script attempts to recompute unset `parent_course` relations in the given semesters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters for which you want to recompute `parent_course`
            references, i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
            If this argument is omitted, `parent_course` references are only recomputed for
            the current semester. If you pass "all" to this argument, this script will recompute
            `parent_course` for all semesters found in Courses in the db.
                """
            ),
            default=None,
        )

        parser.add_argument(
            "--overwrite-manual-changes",
            action="store_true",
            default=False,
            help=dedent(
                """
                CAUTION: If this flag is included, this script will overwrite all manual changes
                made to `parent_course` links of courses in this semester.
                """
            ),
        )

    def handle(self, *args, **kwargs):
        semesters = get_semesters(kwargs["semesters"])
        overwrite_manual = kwargs["overwrite_manual_changes"]

        if overwrite_manual:
            confirm = input(
                "Are you sure you want to overwrite all manual changes? (y/N): "
            )
            if confirm.lower() != "y":
                print("Operation cancelled by user.")
                return 1

        recompute_parent_courses(
            semesters, overwrite_manual_changes=overwrite_manual, verbose=True
        )
