import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses import registrar
from courses.models import Course, Section
from courses.util import get_course_and_section, get_current_semester


def set_all_status(semester=None):
    if semester is None:
        semester = get_current_semester()
    statuses = registrar.get_all_course_status(semester)
    if not statuses:
        return
    for status in tqdm(statuses):
        section_code = status.get("section_id_normalized")
        if section_code is None:
            continue

        try:
            _, section = get_course_and_section(section_code, semester)
        except (Section.DoesNotExist, Course.DoesNotExist):
            continue
        section.status = status["status"]
        section.save()


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        set_all_status(semester=kwargs["semester"])
