import json
import re
from os import listdir, path
from textwrap import dedent
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from degree.models import Degree, program_code_to_name
from degree.utils.parse_degreeworks import parse_degreeworks


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

    def handle(self, *args, **kwargs):
        directory = kwargs["directory"]
        assert path.isdir(directory), f"{directory} is not a directory"

        for degree_file in listdir(directory):
            year, program, degree, major, concentration = re.match(
                r"(\d+)-(\w+)-(\w+)-(\w+)(?:-(\w+))?", degree_file
            ).groups()
            if program not in program_code_to_name:
                print(f"Skipping {degree_file} because {program} is not an applicable program code")
                continue
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

                degree.save()

                with open(path.join(directory, degree_file)) as f:
                    degree_json = json.load(f)

                rules = parse_degreeworks(degree_json, degree)
                print(f"Saving degree {degree}...")
                for rule in rules:
                    rule.degree = degree
                    rule.save()
