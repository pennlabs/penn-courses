import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses import registrar
from courses.management.commands.loadstatus import set_all_status
from courses.management.commands.recompute_parent_courses import (
    recompute_parent_courses,
)
from courses.management.commands.recompute_soft_state import recompute_soft_state
from courses.models import Department, Section
from courses.util import get_current_semester, upsert_course_from_opendata
from review.management.commands.clearcache import clear_cache
from review.management.commands.precompute_pcr_views import precompute_pcr_views


def registrar_import(semester=None, query=""):
    if semester is None:
        semester = get_current_semester()
    semester = semester.upper()

    print("Loading in courses with prefix %s from %s..." % (query, semester))
    results = registrar.get_courses(query, semester)

    missing_sections = set(
        Section.objects.filter(course__semester=semester).values_list("id", flat=True)
    )
    for info in tqdm(results):
        upsert_course_from_opendata(info, semester, missing_sections)
    Section.objects.filter(id__in=missing_sections).update(status="X")

    print("Updating department names...")
    departments = registrar.get_departments()
    for dept_code, dept_name in tqdm(departments.items()):
        dept, _ = Department.objects.get_or_create(code=dept_code)
        dept.name = dept_name
        dept.save()

    print("Loading course statuses from registrar...")
    set_all_status(semester=semester, add_status_update=True)

    recompute_parent_courses(semesters=[semester], verbose=True)
    recompute_soft_state(semesters=[semester], verbose=True)

    if semester.endswith("C"):
        # Make sure to load in summer course data as well
        # (cron job only does current semester, which is either fall or spring)
        registrar_import(semester=semester[:-1] + "B", query=query)

    precompute_pcr_views(verbose=True, is_new_data=False)


class Command(BaseCommand):
    help = "Load in courses, sections and associated models from the Penn registrar and requirements data sources."  # noqa: E501

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)
        parser.add_argument("--query", default="")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        semester = kwargs.get("semester")
        query = kwargs.get("query")

        registrar_import(semester, query)

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
