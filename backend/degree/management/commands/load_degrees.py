import json
import re
from os import listdir, path
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.degree.utils.parse_degreeworks import parse_and_save_degreeworks
from degree.management.commands.deduplicate_rules import deduplicate_rules
from degree.models import Degree, program_code_to_name


class Command(BaseCommand):
    help = dedent(
        """
        Load degrees from degreeworks JSONs named like year-program-degree-major-concentration
        (without the .json extension). Note that this command deletes any existing degrees that
        overlap with the new degrees to be loaded.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            required=True,
            help=dedent(
                """
                A directory containing JSON files of degrees, assumed to be named like
                year-program-degree-major-concentration.json.
                """
            ),
        )

        parser.add_argument(
            "--deduplicate-rules",
            action="store_true",
        )

        super().add_arguments(parser)

    def handle(self, *args, **kwargs):
        directory = kwargs["directory"]
        assert path.isdir(directory), f"{directory} is not a directory"

        created_count = 0
        for degree_file in listdir(directory):
            degree_match = re.match(r"(\d+)-(\w+)-(\w+)-(\w+)(?:-(\w+))?", degree_file)
            if not degree_match:
                if kwargs["verbosity"]:
                    print(
                        "Skipping {degree_file} because its name does not "
                        "follow the format of a degree file."
                    )
                continue
            year, program, degree, major, concentration = degree_match.groups()
            if program not in program_code_to_name:
                if kwargs["verbosity"]:
                    print(
                        f"Skipping {degree_file} because {program} "
                        "is not an applicable program code"
                    )
                continue

            if kwargs["verbosity"]:
                print("Loading", degree_file, "...")

            with transaction.atomic():
                Degree.objects.filter(
                    program=program,
                    degree=degree,
                    major=major,
                    concentration=concentration,
                    year=year,
                ).delete()

                degree = Degree(
                    program=program,
                    degree=degree,
                    major=major,
                    concentration=concentration,
                    year=year,
                )

                with open(path.join(directory, degree_file)) as f:
                    degree_json = json.load(f)

                if kwargs["verbosity"]:
                    print(f"Parsing and saving degree {degree}...")
                created_count += parse_and_save_degreeworks(degree_json, degree)

        if kwargs["verbosity"]:
            print(f"Created {created_count} degrees")

        if kwargs["deduplicate_rules"]:
            if kwargs["verbosity"]:
                print("Deduplicating rules...")
            deduplicate_rules(verbose=kwargs["verbosity"])
