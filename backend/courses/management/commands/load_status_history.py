import csv
import os
from datetime import datetime, timedelta

import pytz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils.timezone import make_aware

from courses.models import Section, StatusUpdate


class Command(BaseCommand):
    help = (
        "Load course status history into the database from a CSV file with the 5 columns:\n"
        "full_code, semester, created_at (%Y-%m-%d %H:%M:%S.%f %Z), old_status, new_status. "
    )

    def add_arguments(self, parser):
        parser.add_argument("--src", type=str, default="")

    def handle(self, *args, **kwargs):
        src = os.path.abspath(kwargs["src"])
        _, file_extension = os.path.splitext(kwargs["src"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        sections_map = dict()  # maps (full_code, semester) to section id
        with open(src) as history_file:
            history_reader = csv.reader(history_file)
            sections_to_fetch = set()
            for row in history_reader:
                sections_to_fetch.add((row[0], row[1]))
            full_codes = [sec[0] for sec in sections_to_fetch]
            semesters = [sec[1] for sec in sections_to_fetch]
            section_obs = Section.objects.filter(
                full_code__in=full_codes, course__semester__in=semesters
            ).annotate(semester=F("course__semester"))
            for section_ob in section_obs:
                sections_map[section_ob.full_code, section_ob.semester] = section_ob.id
            row_count = sum(1 for _ in history_reader)
        print(
            "This script is atomic, meaning either all the status updates from the given "
            "CSV will be loaded into the database, or otherwise if an error is encountered, "
            "all changes will be rolled back and the database will remain as it was "
            "before the script was run."
        )
        with transaction.atomic():
            with open(src) as history_file:
                print(f"Beginning to load status history from {src}")
                history_reader = csv.reader(history_file)
                i = 0
                added_num = 0
                to_save = []
                for row in history_reader:
                    i += 1
                    if i % 100 == 1:
                        print(f"Loading status history... ({i} / {row_count})")
                    full_code = row[0]
                    semester = row[1]
                    created_at = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f %Z")
                    created_at = make_aware(created_at, timezone=pytz.utc, is_dst=None)
                    old_status = row[3]
                    new_status = row[4]
                    if old_status != "O" and old_status != "C" and old_status != "X":
                        old_status = ""
                    if new_status != "O" and new_status != "C" and new_status != "X":
                        new_status = ""
                    if (full_code, semester) not in sections_map.keys():
                        raise ValueError(f"Section {full_code} {semester} not found in db.")
                    section_id = sections_map[full_code, semester]
                    if not StatusUpdate.objects.filter(
                        section_id=section_id,
                        old_status=old_status,
                        new_status=new_status,
                        created_at__gte=created_at - timedelta(seconds=0.1),
                        created_at__lte=created_at + timedelta(seconds=0.1),
                    ).exists():
                        added_num += 1
                        status_update = StatusUpdate(
                            section_id=section_id,
                            old_status=old_status,
                            new_status=new_status,
                            created_at=created_at,
                        )
                        to_save.append(status_update)
                StatusUpdate.objects.bulk_create(to_save)
        print(
            f"Finished loading status history from {src}... processed {row_count} rows. "
            f"Added {added_num} status updates to the database."
        )