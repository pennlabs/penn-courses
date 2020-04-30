import logging

from django.core.management.base import BaseCommand
from options.models import get_value
from tqdm import tqdm

from alert.views import alert_for_course
from courses import registrar


class Command(BaseCommand):
    help = "Load course status for courses in the DB"

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        semester = get_value("SEMESTER")
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

            # _, section = get_course_and_section(course_id, semester)

            should_send_alert = course_status == "O" and semester == course_term

            if should_send_alert:
                try:
                    alert_for_course(course_id, semester=course_term, sent_by="WEB")
                    stats["sent"] += 1
                except ValueError:
                    stats["parse_error"] += 1
            else:
                stats["skipped"] += 1

        print(stats)
