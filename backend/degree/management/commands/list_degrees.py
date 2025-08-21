from dataclasses import asdict
from os import getenv
from dotenv import load_dotenv
from pprint import pprint
from textwrap import dedent
from django.forms.models import model_to_dict
from django.core.management.base import BaseCommand

from degree.utils.degreeworks_client import DegreeworksClient
from courses.util import get_current_semester


class Command(BaseCommand):
    help = dedent(
        """
        Lists the available degrees for a semester.

        Expects PENN_ID, X_AUTH_TOKEN, REFRESH_TOKEN, NAME environment variables are set. It is
        recommended you add a .env file to the backend and let pipenv load it in for you.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--out-file",
            help=dedent(
                """
                A .json to write out the degrees to
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
                The minimum year to list degrees from.
                """
            ),
        )

        parser.add_argument(
            "--to-year",
            type=int,
            help=dedent(
                """
                The max year to list degrees from. If this is not provided, then degrees
                are listed until the current year (as provided by get_current_semester).
                """
            ),
        )

    def handle(self, *args, **kwargs):
        out_handle = open(kwargs["out_file"], "w") if kwargs["out_file"] is not None else None

        since_year = kwargs["since_year"]
        to_year = kwargs["to_year"] or int(get_current_semester()[:4])

        print(out_handle)
        print(since_year)
        print(to_year)

        load_dotenv()

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
                for degrees in client.degrees_of(program, year=year):
                    print(type(degrees))
                    if out_handle is not None:
                        out_handle.write(str(model_to_dict(degrees)))
                    pprint(degrees, width=-1)

        if out_handle is not None:
            out_handle.close()
