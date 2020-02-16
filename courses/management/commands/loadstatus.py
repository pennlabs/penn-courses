import logging

from django.core.management.base import BaseCommand

from courses.tasks import set_all_status


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        set_all_status(semester=kwargs["semester"])
