import logging

from django.core.management.base import BaseCommand

from courses.tasks import load_requirements


class Command(BaseCommand):
    help = """
Load in courses, sections and associated models from the Penn registrar and requirements
data sources.
    """

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)
        parser.add_argument("--school", nargs="?", default="")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        print(
            f'Loading requirements for school {kwargs["school"]} and semester {kwargs["semester"]}'
        )
        load_requirements(school=kwargs["school"], semester=kwargs["semester"])
