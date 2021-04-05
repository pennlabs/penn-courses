import os
from textwrap import dedent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.management.commands.export_anon_registrations import get_semesters
from courses.models import StatusUpdate
from PennCourses.settings.base import S3_resource


class Command(BaseCommand):
    help = (
        "Export Status Updates by semester with the 5 columns:\n"
        "full_code, semester, created_at (%Y-%m-%d %H:%M:%S.%f %Z), old_status, new_status"
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
            If you pass "all" to this argument, this script will export all status updates.
                """
            ),
            default="",
        )

    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        upload_to_s3 = kwargs["upload_to_s3"]
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if len(semesters) == 0:
            raise ValueError("No semesters provided for status update export.")
        assert path.endswith(".csv") or path == os.devnull
        
        script_print_path = ("s3://penn.courses/" if upload_to_s3 else "") + path
        print(f"Generating {script_print_path} with status updates from semesters {semesters}...")
        rows = 0
        output_file_path = "/app/export_status_history_output.csv" if upload_to_s3 else path
        with open(output_file_path, "w") as output_file:
            for update in tqdm(
                StatusUpdate.objects.filter(section__course__semester__in=semesters)
                .select_related("section")
                .order_by("created_at")
            ):
                rows += 1
                output_file.write(
                    f"{update.section.full_code},{update.section.semester},"
                    f"{update.created_at.strftime('%Y-%m-%d %H:%M:%S.%f %Z')},"
                    f"{update.old_status},{update.new_status}\n"
                )
        if upload_to_s3:
            S3_resource.meta.client.upload_file(
                "/app/export_status_history_output.csv", "penn.courses", path
            )
            os.remove("/app/export_status_history_output.csv")
        print(f"Generated {script_print_path} with {rows} rows...")
