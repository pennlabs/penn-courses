import gc
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from alert.management.commands.recomputestats import garbage_collect_topics
from courses.management.commands.load_crosswalk import load_crosswalk
from courses.models import Course
from courses.util import get_semesters
from review.management.commands.clearcache import clear_cache


def fill_topics(verbose=False):
    if verbose:
        print("Filling courses without topics...")
    filled = 0
    for course in tqdm(Course.objects.filter(topic__isnull=True).order_by("semester")):
        if not course.topic:
            filled += 1
            course.save()
            gc.collect()
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
            "--semesters",
            type=str,
            help=dedent(
                """
                A comma-separated list of semesters for which you want to reset courses' topics,
                e.g. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
                If this argument is omitted, no topics will be deleted (topics will only be
                computed/linked for courses not already linked to a topic).
                If you pass "all" to this argument, this script will delete/recompute all topics.
                """
            ),
            nargs="?",
            default=None,
        )

    def handle(self, *args, **kwargs):
        print(
            "This script is atomic, meaning either all Topic links will be added to the database, "
            "or otherwise if an error is encountered, all changes will be rolled back and the "
            "database will remain as it was before the script was run."
        )

        semesters = kwargs["semesters"] and get_semesters(semesters=kwargs["semesters"])

        with transaction.atomic():
            if semesters:
                Course.objects.filter(semester__in=semesters).update(topic=None)

            garbage_collect_topics()
            fill_topics(verbose=True)
            load_crosswalk(print_missing=False, verbose=True)

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
