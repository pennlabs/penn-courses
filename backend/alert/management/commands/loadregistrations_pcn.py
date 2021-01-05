import logging
import mmap
import os

import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.models import Registration, Section
from courses.models import Course, Department
from courses.util import get_current_semester


tqdm.pandas()  # enables progress bars for pandas operations


def get_num_lines(file_path):
    """
    Returns the number of lines in the file at the given path.
    """
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines


def load_pcn_registrations(courserequest_path, courseinfo_path, dummy_missing_sections=False):
    """
    :param courserequest_path: Path to the courserequest.csv file from PCN.
    :param courseinfo_path: Path to the courseinfo.csv file from PCN.
    :param dummy_missing_sections: Set to True to fill in missing sections with dummy info
        (only containing dept_code, course_code, section_code, and semester).
    """
    print("Checking given CSVs (nothing will be added to the database until indicated later)...")

    courserequest = pd.read_csv(courserequest_path)
    courseinfo = pd.read_csv(courseinfo_path)

    table = courserequest.merge(courseinfo, how="inner", left_on="course", right_on="key")
    table["notification_sent"] = table["status"] == "complete"
    error_message = ""

    def get_date(date, column):
        nonlocal error_message
        cantidate_error_message = (
            f"String '{date}' in the '{column}' column in {courserequest_path} "
            "could not be parsed to a datetime object."
        )
        dt = None
        try:
            dt = parse_datetime(date)
        except ValueError:
            error_message = cantidate_error_message
        if dt is None:
            error_message = cantidate_error_message
        if error_message != "":
            raise ValueError
        return make_aware(dt)

    print("Parsing created dates...")
    try:
        table["created_at"] = table["created"].progress_map(lambda x: get_date(x, "created"))
    except ValueError:
        print("\n\n")
        print(error_message)
        return False
    print("Parsing updated dates...")
    try:
        table["notification_sent_at"] = table.progress_apply(
            (lambda row: get_date(row["updated"], "updated") if row["notification_sent"] else None),
            axis=1,
        )
    except ValueError:
        print("\n\n")
        print(error_message)
        return False

    def get_semester(created, created_at):
        nonlocal error_message
        if 3 <= created_at.month and created_at.month <= 9:
            sem = str(created_at.year) + "C"
        else:
            if created_at.month < 3:
                sem = str(created_at.year) + "A"
            else:
                sem = str(created_at.year + 1) + "A"
        if sem >= get_current_semester():
            error_message = (
                "PCN registrations from the current semester or later cannot be imported. "
                f"Datetime '{created}' in column 'created' is from the current semester."
            )
            raise ValueError
        return sem

    searched_for_sections = dict()

    def find_section(row):
        nonlocal error_message
        dept_code = row["course_y"].strip().split("-")[0].upper()
        course_code = row["course_y"].strip().split("-")[1]
        section_code = row["course_y"].strip().split("-")[2]
        semester = get_semester(row["created"], row["created_at"])
        full_code = f"{dept_code}-{course_code}-{section_code}"
        try:
            if f"{full_code} {semester}" in searched_for_sections:
                found_section = searched_for_sections[f"{full_code} {semester}"]
            else:
                found_section = Section.objects.get(
                    course__department__code=dept_code,
                    course__code=course_code,
                    code=section_code,
                    course__semester=semester,
                )
                searched_for_sections[f"{full_code} {semester}"] = found_section
        except ObjectDoesNotExist:
            found_section = None
            searched_for_sections[f"{full_code} {semester}"] = None
        if found_section is None:
            if not dummy_missing_sections:
                error_message = (
                    f"Section {dept_code}-{course_code}-{section_code} {semester} "
                    f"('{row['course_y']}' in column 'course' of courseinfo.csv) does not exist in "
                    "database and dummy_missing_sections is not flagged"
                )
                raise ValueError
            return None
        if Registration.objects.filter(section=found_section,
                                       created_at=row["created_at"],
                                       notification_sent=row["notification_sent"],
                                       notification_sent_at=row["notification_sent_at"]).exists():
            error_message = (
                f"A registration with section {dept_code}-{course_code}-{section_code} {semester}, "
                f"'created'='{row['created']}' and 'updated'='{row['updated']}' already exists in "
                "database. Did you accidentally run this script twice?"
            )
            raise ValueError
        return found_section.id

    print("Checking if specified sections exist in database...")
    try:
        table["found_section_id"] = table.progress_apply(lambda row: find_section(row), axis=1)
    except ValueError:
        print("\n\n")
        print(error_message)
        return False

    table = table[
        ["notification_sent", "notification_sent_at", "created_at", "found_section_id", "course_y"]
    ]

    table.to_csv("test_csv.csv")

    print("Verification succeeded! Proceeding to load registrations (adding to database)...")

    num_dummy_sections = 0

    created_sections = dict()

    for index, row in tqdm(table.iterrows(), total=table.shape[0]):
        if pd.isna(row["found_section_id"]):
            dept_code = row["course_y"].strip().split("-")[0].upper()
            course_code = row["course_y"].strip().split("-")[1]
            section_code = row["course_y"].strip().split("-")[2]
            semester = get_semester("", row["created_at"])
            full_code = f"{dept_code}-{course_code}-{section_code}"
            if f"{full_code} {semester}" in created_sections:
                section = created_sections[f"{full_code} {semester}"]
            else:
                num_dummy_sections += 1
                dept, _ = Department.objects.get_or_create(code=dept_code)
                course, _ = Course.objects.get_or_create(
                    department=dept, code=course_code, semester=semester
                )
                section = Section(
                    course=course,
                    code=section_code,
                    full_code=f"{dept_code}-{course_code}-{section_code}",
                )
                section.save()
                created_sections[f"{full_code} {semester}"] = section
        else:
            section = Section.objects.get(id=row["found_section_id"])
        if row["notification_sent"]:
            registration = Registration(
                section=section,
                notification_sent=row["notification_sent"],
                notification_sent_at=row["notification_sent_at"],
                source="SCRIPT_PCN"
            )
        else:
            registration = Registration(section=section,
                                        notification_sent=row["notification_sent"],
                                        source="SCRIPT_PCN")
        registration.save()
        registration.created_at = row["created_at"]
        registration.original_created_at = None
        registration.save()

    print(
        f"Done! {table.shape[0]} registrations and {num_dummy_sections} dummy sections "
        "added to database."
    )


class Command(BaseCommand):
    help = "Load in PCN registrations from a csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "courserequest_path", type=str, help="The path to courserequest.csv from PCN."
        )
        parser.add_argument(
            "courseinfo_path", type=str, help="The path to courseinfo.csv from PCN."
        )

        parser.add_argument(
            "--dummy_missing_sections",
            action="store_true",
            help=(
                "Flag to fill in missing sections with dummy info (only containing "
                "dept_code, course_code, section_code, and semester). "
                "It is recommended to include this flag."
            ),
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        courserequest_path = os.path.abspath(kwargs["courserequest_path"])
        cr_bname = os.path.basename(courserequest_path)
        if cr_bname != "courserequest.csv":
            return f"courserequest filename is {cr_bname}, should be courserequest.csv."
        courseinfo_path = os.path.abspath(kwargs["courseinfo_path"])
        ci_bname = os.path.basename(courseinfo_path)
        if ci_bname != "courseinfo.csv":
            return f"courseinfo filename is {ci_bname}, should be courseinfo.csv."
        print(f"Loading PCN registrations from {courserequest_path} and {courseinfo_path}")
        load_pcn_registrations(
            courserequest_path=courserequest_path,
            courseinfo_path=courseinfo_path,
            dummy_missing_sections=kwargs["dummy_missing_sections"],
        )
