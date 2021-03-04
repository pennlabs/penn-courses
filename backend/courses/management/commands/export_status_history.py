import operator

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.models import StatusUpdate


class Command(BaseCommand):
    help = (
        "Export Status Updates by semester with the 5 columns:\n"
        "full_code, semester, created_at, old_status, new_status"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path", type=str, help="The path to the csv you want to export to."
        )
        parser.add_argument(
            "semester", type=str, help="The semester from which to take Status Updates."
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]
        semester = kwargs["semester"]
        assert file_path.endswith(".csv")
        print(f"Generating {file_path} with status updates from semester {semester}...")
        rows = 0
        with open(file_path, "w") as output_file:
            for update in tqdm(
                sorted(
                    StatusUpdate.objects.filter(section__course__semester=semester),
                    key=operator.attrgetter("created_at"),
                )
            ):
                rows += 1
                output_file.write(
                    f"{update.section.full_code},{update.section.semester},"
                    f"{update.created_at},{update.old_status},{update.new_status}\n"
                )
        print(f"Generated {file_path} with {rows} rows...")
