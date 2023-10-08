
from textwrap import dedent

from django.core.management.base import BaseCommand

from degree.degreeworks.request_degreeworks import degree_plans_of, get_programs

class Command(BaseCommand):
    help = "Remove duplicate/redundant status updates from the given semesters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters for which you want to remove duplicate/redundant
            status updates, i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
            If this argument is omitted, stats are only recomputed for the current semester.
            If you pass "all" to this argument, this script will remove duplicate/redundant
            status updates for all semesters found in Courses in the db.
                """
            ),
            nargs="?",
            default=None,
        )

    def handle(self, *args, **kwargs):
        pass