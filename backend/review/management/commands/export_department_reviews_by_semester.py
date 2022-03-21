import json
import os
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db.models import OuterRef

from alert.management.commands.recomputestats import get_semesters
from courses.models import Department
from PennCourses.settings.base import S3_resource
from review.annotations import review_averages


def average_by_dept(fields, semesters, departments=None, path=None, verbose=False):
    """
    For each department and year, compute the average of given fields
    (see `alert.models.ReviewBit` for an enumeration of fields) across all (valid) sections.
    Note that fields should be a list of strings representing the review fields to be aggregated.
    """
    dept_avgs = {}

    for i, semester in enumerate(semesters):
        if verbose:
            print(f"Processing semester {semester} ({i+1}/{len(semesters)})")
        if departments is None:
            depts_qs = Department.objects.all()
        else:
            depts_qs = Department.objects.filter(code__in=departments)
        semester_dept_avgs = review_averages(
            depts_qs,
            fields=fields,
            subfilters={
                "review__section__course__semester": semester,
                "review__section__course__department_id": OuterRef("id"),
            },
            extra_metrics=False,
        ).values("code", *fields)

        dept_avgs[semester] = {dept_dict.pop("code"): dept_dict for dept_dict in semester_dept_avgs}

    return dept_avgs


class Command(BaseCommand):
    help = dedent(
        """
        Compute the average of given `fields`
        (see `alert.models.ReviewBit` for an enumeration of fields)
        by semester by department, and print or save to a file.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fields",
            nargs="?",
            default=None,
            help=dedent(
                """
                fields as strings seperated by commas. If not provided, defaults to
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
        parser.add_argument(
            "--upload_to_s3",
            default=False,
            action="store_true",
            help=(
                "Enable this argument to upload the output of this script to the penn.courses "
                "S3 bucket, at the path specified by the path argument."
            ),
        )
        parser.add_argument(
            "--semesters",
            nargs="?",
            default="all",
            type=str,
            help=dedent(
                """
                semesters to aggregate data for (in XXXXx form) as strings seperated
                by commas. If semesters not provided then all semesters used.
                """
            ),
        )
        parser.add_argument(
            "--departments",
            nargs="?",
            default=None,
            type=str,
            help=dedent(
                """
                department codes to aggregate data for as strings seperated by
                commas. If departments not provided then all departments used.
                """
            ),
        )

    def handle(self, *args, **kwargs):
        upload_to_s3 = kwargs["upload_to_s3"]
        path = kwargs["path"]
        assert path is None or (path.endswith(".json") and "/" not in path)
        semesters = get_semesters(semesters=kwargs["semesters"])

        if kwargs["fields"] is None:
            fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]
        else:
            fields = kwargs["fields"].strip().split(",")
        if kwargs["departments"] is None:
            departments = None
        else:
            departments = kwargs["departments"].strip().split(",")

        print(
            f"Averaging department review data ({', '.join(fields)}) by semester "
            f"for semester(s): {', '.join(semesters)}"
        )

        dept_avgs = average_by_dept(
            fields, semesters=semesters, departments=departments, verbose=True
        )

        if path is None:
            print(json.dumps(dept_avgs, indent=4))
        else:
            output_file_path = (
                "/tmp/review_semester_department_export.json" if upload_to_s3 else path
            )
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            with open(output_file_path, "w") as f:
                json.dump(dept_avgs, f, indent=4)

            if upload_to_s3:
                S3_resource.meta.client.upload_file(output_file_path, "penn.courses", path)
                os.remove(output_file_path)
