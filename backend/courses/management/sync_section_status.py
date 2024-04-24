import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Course, Section
from courses import registrar
from courses.util import (
    get_course_and_section,
    get_current_semester,
    record_update,
    translate_semester_inv,
)


class Command(BaseCommand):
    help = """
        Find any discrepancies between a section's status and the section status included
        on OpenData's API and update the db accordingly. Note that this operates differently
        from webhookbackup and doesn't send any alerts – this just syncs section statuses.
    """

    def handle(self, *args, **options):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        semester = get_current_semester()
        statuses = registrar.get_all_course_status(semester)
        resync_count = 0

        for status in tqdm(statuses):
            data = status
            section_code = data.get("section_id_normalized")
            if section_code is None:
                continue

            course_status = data.get("status")
            if course_status is None:
                continue

            course_term = data.get("term")
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
            if last_status_update != course_status or current_status != course_status:
                resync_count += 1

            # Change status attribute of section model (might want to use bulk update)
            if current_status != course_status:
                section.status = course_status
                section.save()

            # Add corresponding status update object
            if last_status_update.new_status != course_status:
                record_update(
                    section,
                    course_term,
                    last_status_update.new_status,
                    course_status,
                    False,
                    json.dumps(data),
                )

        print(f"Statuses for {resync_count} courses have been resynced.")
