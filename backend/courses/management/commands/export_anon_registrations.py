import os
from textwrap import dedent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Registration
from courses.models import Course
from PennCourses.settings.base import S3_resource


def get_semesters(semesters, verbose=False):
    """
    Validate a given string semesters argument, and return a list of the individual string semesters
    specified by the argument.
    """
    possible_semesters = set(Course.objects.values_list("semester", flat=True).distinct())
    if semesters == "all":
        semesters = list(possible_semesters)
    else:
        semesters = [sem.strip() for sem in semesters.split(",") if len(sem.strip()) > 0]
        for s in semesters:
            if s not in possible_semesters:
                raise ValueError(f"Provided semester {s} was not found in the db.")
    return semesters


class Command(BaseCommand):
    help = (
        "Export anonymized PCA Registrations by semester with the 14 columns:\n"
        "registration.section.course.department.code, registration.section.course.code,"
        "registration.section.code, registration.section.semester, registration.created_at, "
        "registration.original_created_at, registration.id, resubscribed_from_id, "
        "registration.notification_sent, notification_sent_at, registration.cancelled, "
        "registration.cancelled_at, registration.deleted, registration.deleted_at"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="The path (local or in S3) you want to export to (must be a .csv file).",
        )
        parser.add_argument(
            "--upload_to_s3",
            default=False,
            action="store_true",
            help=(
                "Enable this argument to upload the output of this script to the penn.courses "
                "S3 bucket, at the path specified by the path argument. "
            ),
        )
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters from which you want to export PCA registrations,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
            If you pass "all" to this argument, this script will export all PCA registrations.
                """
            ),
            default="",
        )

    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        upload_to_s3 = kwargs["upload_to_s3"]
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if len(semesters) == 0:
            raise ValueError("No semesters provided for registration export.")
        assert path.endswith(".csv") or path == os.devnull

        script_print_path = ("s3://penn.courses/" if upload_to_s3 else "") + path
        print(
            f"Generating {script_print_path} with registration data from "
            f"semesters {semesters}..."
        )
        rows = 0
        output_file_path = "/app/export_anon_registrations.csv" if upload_to_s3 else path
        with open(output_file_path, "w") as output_file:
            for registration in tqdm(
                Registration.objects.filter(section__course__semester__in=semesters)
                .select_related("section", "section__course", "section__course__department")
                .order_by("created_at")
            ):
                resubscribed_from_id = (
                    str(registration.resubscribed_from_id)
                    if registration.resubscribed_from is not None
                    else ""
                )
                notification_sent_at = (
                    str(registration.notification_sent_at)
                    if registration.notification_sent_at is not None
                    else ""
                )
                rows += 1
                output_file.write(
                    f"{registration.section.course.department.code},"
                    f"{registration.section.course.code},{registration.section.code},"
                    f"{registration.section.semester},{registration.created_at},"
                    f"{registration.original_created_at},{registration.id},{resubscribed_from_id},"
                    f"{registration.notification_sent},{notification_sent_at},"
                    f"{registration.cancelled},{registration.cancelled_at},{registration.deleted},"
                    f"{registration.deleted_at}\n"
                )
        if upload_to_s3:
            S3_resource.meta.client.upload_file(
                "/app/export_anon_registrations.csv", "penn.courses", path
            )
            os.remove("/app/export_anon_registrations.csv")
        print(f"Generated {script_print_path} with {rows} rows...")
