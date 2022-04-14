from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.management.commands.load_crosswalk import load_crosswalk
from courses.models import Course, Topic
from review.management.commands.clearcache import clear_cache


def fill_topics(verbose=False):
    if verbose:
        print("Filling courses without topics...")
    filled = 0
    for course in tqdm(Course.objects.all().order_by("semester").select_related("topic")):
        if not course.topic:
            filled += 1
            course.save()
    if verbose:
        print(f"Filled the topic field of {filled} courses.")


class Command(BaseCommand):
    help = (
        "This script remakes Topics by saving courses in chronological order "
        "(relying on the behavior of `Course.save()`), and then runs "
        "`load_crosswalk` (all in a single transaction)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help=dedent(
                """
                Delete all Topics and remake from scratch.
                """
            ),
        )

    def handle(self, *args, **kwargs):
        print(
            "This script is atomic, meaning either all Topic links will be added to the database, "
            "or otherwise if an error is encountered, all changes will be rolled back and the "
            "database will remain as it was before the script was run."
        )

        delete = kwargs["delete"]

        with transaction.atomic():
            if delete:
                to_delete = Topic.objects.all()
                prompt = input(
                    f"This script will delete all Topic objects ({to_delete.count()} total). "
                    "Proceed? (y/N) "
                )
                if prompt.strip().upper() != "Y":
                    return
                to_delete.delete()

            fill_topics(verbose=True)
            load_crosswalk(print_missing=False, verbose=True)

        print("Clearing cache")
        clear_cache()
