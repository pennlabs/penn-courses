import csv
import logging
import os
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from tqdm import tqdm

from courses.models import Section, StatusUpdate
from courses.util import get_semester
from PennCourses.command_utils import get_num_lines


class Command(BaseCommand):
    """
    Input a csv with no header, with a schema of the form:
    full_code, semester, created_at, old_status, new_status

    If you enable the --old_format flag, then input a csv with a header,
    and with a schema of the form:
    old_status, new_status, alert_sent, created_at, department, course_code, section_code

    --dummy_missing_sections
    --fill_in_inconsistencies or smthg
    use section.last_notification_sent_at
    """

    help = "Load course status history from CSV file into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            nargs="?",
            type=str,
            default="",
            help="The path to the CSV containing the status history you want to load.",
        )
        parser.add_argument(
            "--old_format",
            action="store_true",
            type=bool,
            default=False,
            help="Enable this flag to use the old schema (with header, columns = "
            "[old_status, new_status, alert_sent, created_at, department, course_code, "
            "section_code]) rather than the new schema (no header, columns = [full_code, "
            "semester, created_at, old_status, new_status]).",
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        src = os.path.abspath(kwargs["src"])
        old_format = kwargs["old_format"]
        _, file_extension = os.path.splitext(kwargs["src"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        row_count = get_num_lines(src)
        with open(src, newline="") as history_file:
            print(f"beginning to load status history from {src}")
            history_reader = csv.reader(history_file, delimiter=",", quotechar="|")
            iter_reader = iter(history_reader)
            if old_format:
                next(iter_reader)
            for row in tqdm(iter_reader, total=row_count):
                if old_format:
                    section_code = row[4] + "-" + row[5] + "-" + row[6]
                    row[3] += " UTC"
                    row[3] = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S.%f %Z")
                    row[3] = make_aware(row[3], timezone=pytz.utc, is_dst=None)
                    semester = get_semester(row[3])
                    created_at = row[3]
                    if row[0] != "O" and row[0] != "C" and row[0] != "X":
                        row[0] = ""
                    old_status = row[0]
                    if row[1] != "O" and row[1] != "C" and row[1] != "X":
                        row[1] = ""
                    new_status = row[1]
                else:
                    section_code = row[0]
                    semester = row[1]
                    created_at = row[2]
                    created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f %Z")
                    created_at = make_aware(created_at, timezone=pytz.utc, is_dst=None)
                    old_status = row[3]
                    if old_status != "O" and old_status != "C" and old_status != "X":
                        old_status = ""
                    new_status = row[4]
                    if new_status != "O" and new_status != "C" and new_status != "X":
                        new_status = ""
                if Section.objects.filter(
                    full_code=section_code, course__semester=semester
                ).exists():
                    sec = Section.objects.get(full_code=section_code, course__semester=semester,)
                    if not StatusUpdate.objects.filter(
                        section=sec,
                        old_status=old_status,
                        new_status=new_status,
                        alert_sent=False,
                        created_at=created_at,
                    ).exists():
                        status_update = StatusUpdate(
                            section=sec,
                            old_status=old_status,
                            new_status=new_status,
                            alert_sent=False,
                            created_at=created_at,
                        )
                        status_update.save()
        print(f"finished loading status history from {src}...\nprocessed {row_count} rows")
