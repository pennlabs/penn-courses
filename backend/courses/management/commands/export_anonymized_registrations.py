import operator

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Registration


class Command(BaseCommand):
    help = (
        "Export anonymized PCA Registrations by semester with the 9 columns:\n"
        "dept code, course code, section code, semester, created_at, id, resubscribed_from_id, "
        "notification_sent, notification_sent_at"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path", type=str, help="The path to the csv you want to export to."
        )
        parser.add_argument(
            "semester", type=str, help="The semester from which to take Registrations."
        )

    def handle(self, *args, **kwargs):
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
                    f"{registration.section.course.department},{registration.section.course.code},"
                    f"{registration.section.code},{registration.section.semester},"
                    f"{registration.created_at},{registration.id},{resubscribed_from_id},"
                    f"{registration.notification_sent},{notification_sent_at}\n"
                )
        print(f"Generated {file_path} with {rows} rows...")
