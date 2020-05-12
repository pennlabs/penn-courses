import logging

from django.core.management.base import BaseCommand
from options.models import get_value
from tqdm import tqdm

from courses import registrar
from courses.models import Course, Section
from courses.util import get_course_and_section


def set_all_status(semester=None):
    if semester is None:
        semester = get_value("SEMESTER")
    statuses = registrar.get_all_course_status(semester)
    for status in tqdm(statuses):
        if "section_id_normalized" not in status:
            continue

        try:
            _, section = get_course_and_section(status["section_id_normalized"], semester)
        except Section.DoesNotExist:
            continue
        except Course.DoesNotExist:
            continue
        section.status = status["status"]
        section.save()


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        set_all_status(semester=kwargs["semester"])
