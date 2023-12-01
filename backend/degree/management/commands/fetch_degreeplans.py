from os import getenv
from pprint import pprint
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.util import get_current_semester
from degree.models import DegreePlan, program_code_to_name
from degree.utils.degreeworks_client import DegreeworksClient
from degree.utils.parse_degreeworks import parse_degreeworks


class Command(BaseCommand):
    help = dedent(
        """
        Lists the available degreeplans for a semester.

        Expects PENN_ID, X_AUTH_TOKEN, REFRESH_TOKEN, NAME environment variables are set. It is
        recommended you add a .env file to the backend and let pipenv load it in for you.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--degree-plans",
            help=dedent(
                """
            A .json to write out the degreeplans to
            """
            ),
        )

        parser.add_argument(
            "--since-year",
            nargs="?",
            type=int,
            default=2017,
            help=dedent(
                """
            The minimum year to fetch degreeplans from.
            """
            ),
        )

        parser.add_argument(
            "--to-year",
            type=int,
            help=dedent(
                """
            The max year to fetch degreeplans from. If this is not provided, then
            degree plans are listed until the current year (as provided by get_current_semester).
            """
            ),
        )

    def handle(self, *args, **kwargs):
        print(
            dedent(
                """
        Note: this script does not delete any existing degreeplans; you may do that manually using the admin panel
        or `manage.py shell`.
        """
            )
        )

        since_year = kwargs["since_year"]
        to_year = kwargs["to_year"] or int(get_current_semester()[:4])

        pennid = getenv("PENN_ID")
        assert pennid is not None
        auth_token = getenv("X_AUTH_TOKEN")
        assert pennid is not None
        refresh_token = getenv("REFRESH_TOKEN")
        assert refresh_token is not None
        name = getenv("NAME")
        assert name is not None

        client = DegreeworksClient(
            pennid=pennid, auth_token=auth_token, refresh_token=refresh_token, name=name
        )

        for year in range(since_year, to_year + 1):
            for program in client.get_programs(year=year):
                if program not in program_code_to_name:
                    continue
                for degree_plan in client.degree_plans_of(program, year=year):
                    with transaction.atomic():
                        DegreePlan.objects.filter(
                            program=degree_plan.program,
                            degree=degree_plan.degree,
                            major=degree_plan.major,
                            concentration=degree_plan.concentration,
                            year=degree_plan.year,
                        ).all().delete()

                        degree_plan.save()
                        print(f"Saving degree plan {degree_plan}...")
                        rules = parse_degreeworks(client.audit(degree_plan), degree_plan)
                        for rule in rules:
                            rule.degree_plan = degree_plan
                            rule.save()
