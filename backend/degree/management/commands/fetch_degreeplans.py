from os import getenv
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction

from courses.util import get_current_semester
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
                for degree_plan in client.degree_plans_of(program, year=year):
                    with transaction.atomic():
                        parse_degreeworks(client.audit(degree_plan), degree_plan)
