import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Course, Section
from alert.util import should_send_pca_alert
from alert.views import alert_for_course
from courses import registrar
from courses.util import (
    get_course_and_section,
    get_current_semester,
    record_update,
    translate_semester_inv,
    update_course_from_record,
)


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--send_alerts",
            action="store_true",
            help="Include this flag to send status updates",
        )

    def handle(self, *args, **options):
        send_alerts = options["send_alerts"]
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
            course_previous_status = data.get("previous_status") or ""
            if course_status is None:
                stats["missing_data"] += 1
                continue

            course_term = data.get("term")
            if course_term is None:
                stats["missing_data"] += 1
                continue
            if any(course_term.endswith(s) for s in ["10", "20", "30"]):
                course_term = translate_semester_inv(course_term)

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

            alert_for_course_called = False
            if send_alerts and should_send_pca_alert(course_term, course_status):
                try:
                    alert_for_course(
                        section_code,
                        semester=course_term,
                        sent_by="WEB",
                        course_status=course_status,
                    )
                    alert_for_course_called = True
                    stats["sent"] += 1
                except ValueError:
                    stats["parse_error"] += 1
            else:
                stats["skipped"] += 1
            u = record_update(
                section,
                course_term,
                course_previous_status,
                course_status,
                alert_for_course_called,
                data,
            )
            update_course_from_record(u)

        print(stats)
