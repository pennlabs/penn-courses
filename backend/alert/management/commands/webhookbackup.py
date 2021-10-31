import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.util import should_send_pca_alert
from alert.views import alert_for_course
from courses import registrar
from courses.util import get_current_semester


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
            "sent": 0,
            "parse_error": 0,
            "error": 0,
            "skipped": 0,
        }
        for status in tqdm(statuses):
            data = status
            course_id = data.get("course_section", None)
            if course_id is None:
                stats["missing_data"] += 1
                continue

            course_status = data.get("status", None)
            if course_status is None:
                stats["missing_data"] += 1
                continue

            course_term = data.get("term", None)
            if course_term is None:
                stats["missing_data"] += 1
                continue

            prev_status = data.get("previous_status", None)
            if prev_status is None:
                stats["missing_data"] += 1
                continue

            if should_send_pca_alert(course_term, course_status):
                try:
                    alert_for_course(
                        course_id, semester=course_term, sent_by="WEB", course_status=course_status
                    )
                    stats["sent"] += 1
                except ValueError:
                    stats["parse_error"] += 1
            else:
                stats["skipped"] += 1

        print(stats)
