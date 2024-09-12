import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses import registrar
from courses.models import Course, Section
from courses.util import (
    get_course_and_section,
    get_current_semester,
    record_update,
    translate_semester_inv,
)


def set_all_status(semester=None, add_status_update=False):
    if semester is None:
        semester = get_current_semester()
    print(semester)
    statuses = registrar.get_all_course_status(semester)
    if not statuses:
        return
    for status in tqdm(statuses):
        statuses_out_of_sync = []
        status_updates_out_of_sync = []

        section_code = status.get("section_id_normalized")
        if section_code is None:
            continue

        course_status = status.get("status")
        if course_status is None:
            continue

        course_term = status.get("term")
        if course_term is None:
            continue
        if any(course_term.endswith(s) for s in ["10", "20", "30"]):
            course_term = translate_semester_inv(course_term)

        # Ignore sections not in db
        try:
            _, section = get_course_and_section(section_code, semester)
        except (Section.DoesNotExist, Course.DoesNotExist):
            continue

        # Resync database (doesn't need to be atomic)
        last_status_update = section.last_status_update
        current_status = section.status

        # Change status attribute of section model (might want to use bulk update)
        if current_status != course_status:
            statuses_out_of_sync.append(section_code)
            # section.status = course_status
            # section.save()

        # Add corresponding status update object
        if last_status_update.new_status != course_status:
            status_updates_out_of_sync.append(section_code)
            # record_update(
            #     section,
            #     course_term,
            #     last_status_update.new_status,
            #     course_status,
            #     False,
            #     json.dumps(status),
            # )

    print(f"{len(statuses_out_of_sync)} statuses were out of sync.")
    print(statuses_out_of_sync)

    print(f"{len(status_updates_out_of_sync)} status updates were out of sync.")
    print(status_updates_out_of_sync)


class Command(BaseCommand):
    help = "Load course status for courses in the DB. Conditionally adds StatusUpdate objects."

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)
        parser.add_argument(
            "--create-status-updates", action="store_true", help="Create status updates if set"
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        set_all_status(
            semester=kwargs["semester"], add_status_update=kwargs["create_status_updates"]
        )
