import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses import registrar
from courses.management.commands.loadrequirements import load_requirements
from courses.management.commands.loadstatus import set_all_status
from courses.util import get_current_semester, upsert_course_from_opendata


class Command(BaseCommand):
    help = "Load in courses, sections and associated models from the Penn registrar and requirements data sources."  # noqa: E501

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)
        parser.add_argument("--query", nargs="?", default="")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        semester = kwargs.get("semester")
        query = kwargs.get("query")

        if semester is None:
            semester = get_current_semester()

        print("loading in courses with prefix %s from %s..." % (query, semester))
        results = registrar.get_courses(query, semester)

        for course in tqdm(results):
            upsert_course_from_opendata(course, semester)

        print("loading requirements from SEAS...")
        load_requirements(school="SEAS", semester=semester)
        print("loading requirements from Wharton...")
        load_requirements(school="WH", semester=semester)
        print("loading course statuses from registrar...")
        set_all_status(semester=semester)
