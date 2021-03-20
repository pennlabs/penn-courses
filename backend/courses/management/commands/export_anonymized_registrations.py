import logging
import operator

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Registration


class Command(BaseCommand):
    help = "Export anonymized PCA Registrations by semester."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path", type=str, help="The path to the csv you want to export to."
        )
        parser.add_argument(
            "semester", type=str, help="The semester from which to take Registrations."
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        file_path = kwargs["file_path"]
        semester = kwargs["semester"]
        assert file_path.endswith(".csv")
        print(f"Generating {file_path} with registration data from semester {semester}...")
        rows = 0
        with open(file_path, "w") as output_file:
            for registration in tqdm(
                sorted(
                    Registration.objects.filter(section__course__semester=semester),
                    key=operator.attrgetter("created_at"),
                )
            ):
                resubscribed_from_id = (
                    str(registration.resubscribed_from.id)
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
                    f"{registration.section.full_code},{registration.section.semester},"
                    f"{registration.created_at},{notification_sent_at},"
                    f"{registration.id},{resubscribed_from_id}\n"
                )
        print(f"Generated {file_path} with {rows} rows...")
