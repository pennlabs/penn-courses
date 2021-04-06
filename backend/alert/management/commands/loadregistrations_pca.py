import csv
import logging
import os
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.models import Registration, Section
from PennCourses.settings.base import TIME_ZONE


class Command(BaseCommand):
    help = (
        "Load in PCA registrations from a csv file. The csv file must have the following columns:\n"
        "registration.section.full_code, registration.section.semester, "
        "registration.created_at (%Y-%m-%d %H:%M:%S.%f %Z), "
        "registration.original_created_at (%Y-%m-%d %H:%M:%S.%f %Z), "
        "registration.id, resubscribed_from_id, "
        "registration.notification_sent, notification_sent_at (%Y-%m-%d %H:%M:%S.%f %Z), "
        "registration.cancelled, registration.cancelled_at (%Y-%m-%d %H:%M:%S.%f %Z), "
        "registration.deleted, registration.deleted_at (%Y-%m-%d %H:%M:%S.%f %Z)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            type=str,
            default="",
            help="The file path of the .csv file containing the registrations "
            "you want to import",
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        src = os.path.abspath(kwargs["src"])
        _, file_extension = os.path.splitext(kwargs["src"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        print(f"Loading PCA registrations from path {src}")
        print(
            "This script is an atomic transaction, so the database will not be modified "
            "unless the entire script succeeds."
        )

        sections_map = dict()  # maps (full_code, semester) to section id
        registrations_map = dict()  # maps (full_code, semester) to list of registrations
        row_count = 0
        with open(src) as data_file:
            data_reader = csv.reader(data_file, delimiter=",", quotechar='"')
            sections_to_fetch = set()
            for row in data_reader:
                sections_to_fetch.add((row[0], row[1]))
                row_count += 1
            full_codes = [sec[0] for sec in sections_to_fetch]
            semesters = [sec[1] for sec in sections_to_fetch]
            section_obs = (
                Section.objects.filter(full_code__in=full_codes, course__semester__in=semesters)
                .annotate(efficient_semester=F("course__semester"))
                .prefetch_related("registrations")
            )
            for section_ob in section_obs:
                sections_map[section_ob.full_code, section_ob.efficient_semester] = section_ob.id
                registrations_map[section_ob.full_code, section_ob.efficient_semester] = list(
                    section_ob.registrations.all()
                )

        id_corrections = dict()
        semesters = set()
        registrations = []
        with transaction.atomic():
            with open(src) as data_file:
                i = 0
                data_reader = csv.reader(data_file, delimiter=",", quotechar='"')

                for row in tqdm(data_reader, total=row_count):
                    i += 1
                    if len(row) != 12:
                        print(f"\nRow found with {len(row)} (!=12) columns.")
                        print(
                            f"For the above reason, row {i} (1-indexed) of {src} is invalid:\n"
                            f"{row}\n(Not necessarily helpful reminder: Columns must be:\n"
                            "registration.section.full_code, registration.section.semester, "
                            "registration.created_at (%Y-%m-%d %H:%M:%S.%f %Z), "
                            "registration.original_created_at (%Y-%m-%d %H:%M:%S.%f %Z), "
                            "registration.id, resubscribed_from_id, "
                            "registration.notification_sent, "
                            "notification_sent_at (%Y-%m-%d %H:%M:%S.%f %Z), "
                            "registration.cancelled, "
                            "registration.cancelled_at (%Y-%m-%d %H:%M:%S.%f %Z), "
                            "registration.deleted, "
                            "registration.deleted_at (%Y-%m-%d %H:%M:%S.%f %Z)"
                            ")\n\nInvalid input; no registrations were added to the database.\n"
                        )
                        return False

                    full_code = row[0]
                    semester = row[1]
                    if (full_code, semester) not in sections_map:
                        raise ValueError(f"Section {full_code} {semester} not found in database.")
                    semesters.add(semester)

                    original_id = row[4]
                    resubscribed_from_id = row[5]
                    if resubscribed_from_id == "" or resubscribed_from_id == "None":
                        resubscribed_from_id = None

                    def extract_date(dt_string):
                        if dt_string is None or dt_string == "" or dt_string == "None":
                            return None
                        dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f %Z")
                        return make_aware(dt, timezone=pytz.timezone(TIME_ZONE), is_dst=None)

                    registration_dict = dict()  # fields to unpack into Registration initialization
                    registration_dict["section_id"] = sections_map[full_code, semester]
                    registration_dict["source"] = "SCRIPT_PCA"
                    registration_dict["created_at"] = extract_date(row[2])
                    registration_dict["original_created_at"] = extract_date(row[3])
                    registration_dict["notification_sent"] = bool(row[6])
                    registration_dict["notification_sent_at"] = extract_date(row[7])
                    registration_dict["cancelled"] = bool(row[8])
                    registration_dict["cancelled_at"] = extract_date(row[9])
                    registration_dict["deleted"] = bool(row[10])
                    registration_dict["deleted_at"] = extract_date(row[11])

                    registration = Registration(**registration_dict)
                    registration.save(load_script=True)
                    id_corrections[original_id] = registration.id
                    registrations.append((registration, original_id, resubscribed_from_id))

            print("Connecting resubscribe chains...")

            to_save = []
            for registration, original_id, resubscribed_from_id in registrations:
                if resubscribed_from_id is not None:
                    registration.resubscribed_from_id = id_corrections[resubscribed_from_id]
                    to_save.append(registration)
            Registration.objects.bulk_update(to_save, ["resubscribed_from_id"])

            print(f"Done! {len(registrations)} registrations added to database.")
