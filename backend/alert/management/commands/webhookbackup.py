import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Course, Section
from alert.util import should_send_pca_alert
from alert.views import alert_for_course
from courses import registrar
from courses.util import get_course_and_section, get_current_semester


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        semester = get_current_semester()
        statuses = registrar.get_all_course_status(semester)
        stats = {
            "missing_data": 0,
            "section_not_found": 0,
            "duplicate_updates": 0,
            "sent": 0,
            "parse_error": 0,
            "error": 0,
            "skipped": 0,
        }
        for status in tqdm(statuses):
            data = status
            section_code = data.get("section_id_normalized")
            if section_code is None:
                stats["missing_data"] += 1
                continue

            course_status = data.get("status")
            if course_status is None:
                stats["missing_data"] += 1
                continue

            course_term = data.get("term")
            if course_term is None:
                stats["missing_data"] += 1
                continue

            # Ignore sections not in db
            try:
                _, section = get_course_and_section(section_code, semester)
            except (Section.DoesNotExist, Course.DoesNotExist):
                stats["section_not_found"] += 1
                continue

            # Ignore duplicate updates
            last_status_update = section.last_status_update
            if last_status_update and last_status_update.new_status == course_status:
                stats["duplicate_updates"] += 1
                continue

            if should_send_pca_alert(course_term, course_status):
                try:
                    alert_for_course(
                        section_code,
                        semester=course_term,
                        sent_by="WEB",
                        course_status=course_status,
                    )
                    stats["sent"] += 1
                except ValueError:
                    stats["parse_error"] += 1
            else:
                stats["skipped"] += 1

        print(stats)
