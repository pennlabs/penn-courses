import json
import re
from textwrap import dedent

from click import BaseCommand
from django.db.models import OuterRef
from tqdm import tqdm

from alert.management.commands.recomputestats import get_semesters
from courses.models import Department
from review.annotations import review_averages


def average_by_dept(fields, path=None):
    """
    For each department and year, compute the average of given fields
    (see `alert.models.ReviewBit` for an enumeration of fields) across all (valid) sections.
    Note that if fields should be a list of strings representing the review fields to be aggregated.
    """
    dept_avgs = {}
    for semester in tqdm(get_semesters(semesters="all")):
        semester_dept_avgs = review_averages(
            Department.objects.all(),
            fields=fields,
            subfilters={
                "review__section__course__semester": semester,
                "review__section__course__department__id": OuterRef("id"),
            },
            extra_metrics=False,
        ).values("code", *fields)

        dept_avgs[semester] = {dept_dict.pop("code"): dept_dict for dept_dict in semester_dept_avgs}
    if path is None:
        return print(dept_avgs)
    with open(path) as f:
        json.dump(dept_avgs, f)


class Command(BaseCommand):
    help = dedent(
        """
        Compute the average of given `fields`
        (see `alert.models.ReviewBit` for an enumeration of fields)
        by semester by department, and print or save to a file.
        Note that this is an untested and unoptimized command.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fields",
            nargs="?",
            default=None,
            help=dedent(
                """
                fields as strings seperated by whitespace. If fields is not provided, defaults to
                ["course_quality", "difficulty", "instructor_quality", "work_required"].
                """
            ),
        )
        parser.add_argument(
            "--path",
            nargs="?",
            default=None,
            type=str,
            help=dedent(
                """
                path to the output file. If not provided then will simply be printed to console.
                """
            ),
        )

    def handle(self, *args, **kwargs):
        fields = re.split(r"\w", kwargs["fields"])
        if fields is None:
            fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]
        average_by_dept(fields, path=kwargs["path"])
