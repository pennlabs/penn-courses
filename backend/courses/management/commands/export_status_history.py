import os
from textwrap import dedent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.management.commands.export_anon_registrations import get_semesters
from courses.models import StatusUpdate


class Command(BaseCommand):
    help = (
        "Export Status Updates by semester with the 5 columns:\n"
        "full_code, semester, created_at (%Y-%m-%d %H:%M:%S.%f %Z), old_status, new_status"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file_path", type=str, help="The path to the csv you want to export to."
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
        file_path = kwargs["file_path"]
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if len(semesters) == 0:
            raise ValueError("No semesters provided for status update export.")
        assert file_path.endswith(".csv") or file_path == os.devnull
        print(f"Generating {file_path} with status updates from semesters {semesters}...")
        rows = 0
        with open(file_path, "w") as output_file:
            for update in tqdm(
                StatusUpdate.objects.filter(section__course__semester__in=semesters)
                .select_related("section")
                .order_by("created_at")
            ):
                rows += 1
                output_file.write(
                    f"{update.section.full_code},{update.section.semester},"
                    f"{update.created_at.date().strftime('%Y-%m-%d %H:%M:%S.%f %Z')},"
                    f"{update.old_status},{update.new_status}\n"
                )
        print(f"Generated {file_path} with {rows} rows...")
