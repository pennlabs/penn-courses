import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_stats
from courses import registrar
from courses.management.commands.load_crosswalk import load_crosswalk
from courses.management.commands.loadstatus import set_all_status
from courses.management.commands.reset_topics import fill_topics
from courses.models import Department
from courses.util import get_current_semester, upsert_course_from_opendata
from review.management.commands.clearcache import clear_cache


def registrar_import(semester=None, query=""):
    if semester is None:
        semester = get_current_semester()

    print("Loading in courses with prefix %s from %s..." % (query, semester))
    results = registrar.get_courses(query, semester)

    for course in tqdm(results):
        upsert_course_from_opendata(course, semester)

    print("Updating department names...")
    departments = registrar.get_departments()
    for dept_code, dept_name in tqdm(departments.items()):
        dept, _ = Department.objects.get_or_create(code=dept_code)
        dept.name = dept_name
        dept.save()

    print("Loading course statuses from registrar...")
    set_all_status(semester=semester)

    recompute_stats(semesters=semester, verbose=True)

    fill_topics(verbose=True)
    load_crosswalk(print_missing=False, verbose=True)


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

        registrar_import(semester, query)

        print("Clearing cache")
        del_count = clear_cache()
        self.display(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
