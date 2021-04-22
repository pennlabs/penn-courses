import csv
import os
from datetime import datetime

from dateutil.tz import gettz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_percent_open
from alert.models import AddDropPeriod
from courses.models import Section, StatusUpdate
from PennCourses.settings.base import TIME_ZONE


class Command(BaseCommand):
    help = (
        "Load course status history into the database from a CSV file with the 6 columns:\n"
        "full_code, semester, created_at (%Y-%m-%d %H:%M:%S.%f %Z), old_status, new_status, "
        "alert_sent. "
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            type=str,
            default="",
            help="The file path of the .csv file containing the status update "
            "data you want to import",
        )

    def handle(self, *args, **kwargs):
        src = os.path.abspath(kwargs["src"])
        _, file_extension = os.path.splitext(kwargs["src"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        sections_map = dict()  # maps (full_code, semester) to section id
        row_count = 0
        with open(src) as history_file:
            history_reader = csv.reader(history_file)
            sections_to_fetch = set()
            for row in history_reader:
                sections_to_fetch.add((row[0], row[1]))
                row_count += 1
            full_codes = list(set([sec[0] for sec in sections_to_fetch]))
            semesters = list(set([sec[1] for sec in sections_to_fetch]))
            section_obs = Section.objects.filter(
                full_code__in=full_codes, course__semester__in=semesters
            ).annotate(efficient_semester=F("course__semester"))
            for section_ob in section_obs:
                sections_map[section_ob.full_code, section_ob.efficient_semester] = section_ob.id
        add_drop_periods = dict()  # maps semester to AddDropPeriod object
        for adp in AddDropPeriod.objects.filter(semester__in=semesters):
            add_drop_periods[adp.semester] = adp
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
                to_save = []
                for row in tqdm(history_reader, total=row_count):
                    full_code = row[0]
                    semester = row[1]
                    created_at = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f %Z")
                    created_at = make_aware(created_at, timezone=gettz(TIME_ZONE), is_dst=None)
                    old_status = row[3]
                    new_status = row[4]
                    alert_sent = row[5]
                    if old_status != "O" and old_status != "C" and old_status != "X":
                        old_status = ""
                    if new_status != "O" and new_status != "C" and new_status != "X":
                        new_status = ""
                    if (full_code, semester) not in sections_map.keys():
                        raise ValueError(f"Section {full_code} {semester} not found in db.")
                    section_id = sections_map[full_code, semester]
                    status_update = StatusUpdate(
                        section_id=section_id,
                        old_status=old_status,
                        new_status=new_status,
                        created_at=created_at,
                        alert_sent=alert_sent,
                    )
                    status_update.save(add_drop_period=add_drop_periods[semester])
                StatusUpdate.objects.bulk_create(to_save)

            print(f"Finished loading status history from {src}... processed {row_count} rows. ")

            print(
                f"Recomputing PCA Demand Distribution Estimates for {len(semesters)} semesters..."
            )
            recompute_percent_open(semesters=",".join(semesters), verbose=True)
