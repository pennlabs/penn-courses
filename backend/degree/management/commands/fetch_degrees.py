from os import getenv
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from courses.util import get_current_semester
from degree.management.commands.deduplicate_rules import deduplicate_rules
from degree.models import Degree, program_code_to_name
from degree.utils.degreeworks_client import DegreeworksClient
from degree.utils.parse_degreeworks import parse_and_save_degreeworks


class Command(BaseCommand):
    help = dedent(
        """
        Just run this one to get new degrees.

        Fetches, parses and stores degrees from degreeworks.

        Expects PENN_ID, X_AUTH_TOKEN, REFRESH_TOKEN, NAME environment variables are set.

        Note: this script deletes any existing degres in the database that overlap with the
        degrees fetched from degreeworks.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since-year",
            nargs="?",
            type=int,
            default=2017,
            help=dedent(
                """
            The minimum year to fetch degrees from.
            """
            ),
        )

        parser.add_argument(
            "--to-year",
            type=int,
            help=dedent(
                """
            The max year to fetch degrees from. If this is not provided, then degrees are
            listed until the current year (as provided by get_current_semester).
            """
            ),
        )

        parser.add_argument(
            "--deduplicate-rules",
            action="store_true",
        )

    def handle(self, *args, **kwargs):
        print(
            dedent(
                """
            Note: this script deletes any existing degres in the database that overlap with the
            degrees fetched from degreeworks.
            """
            )
        )

        since_year = kwargs["since_year"]
        to_year = kwargs["to_year"] or int(get_current_semester()[:4])

        load_dotenv()

        pennid = getenv("PENN_ID")
        assert pennid is not None
        auth_token = getenv("X_AUTH_TOKEN")
        assert pennid is not None
        refresh_token = getenv("REFRESH_TOKEN")
        assert refresh_token is not None
        name = getenv("NAME")
        assert name is not None

        if kwargs["verbosity"]:
            print("Using Penn ID:", pennid)
            print("Using Auth Token:", auth_token)
            print("Using Refresh Token:", refresh_token)
            print("Using Name:", name)

        client = DegreeworksClient(
            pennid=pennid, auth_token=auth_token, refresh_token=refresh_token, name=name
        )

        for year in range(since_year, to_year + 1):
            for program in client.get_programs(year=year):
                if program not in program_code_to_name:
                    continue
                for degree in client.degrees_of(program, year=year):
                    with transaction.atomic():
                        Degree.objects.filter(
                            program=degree.program,
                            degree=degree.degree,
                            major=degree.major,
                            concentration=degree.concentration,
                            year=degree.year,
                        ).delete()
                        degree.save()
                        if kwargs["verbosity"]:
                            print(f"Saving degree {degree}...")
                        parse_and_save_degreeworks(client.audit(degree), degree)

        if kwargs["deduplicate_rules"]:
            if kwargs["verbosity"]:
                print("Deduplicating rules...")
            deduplicate_rules(verbose=kwargs["verbosity"])
