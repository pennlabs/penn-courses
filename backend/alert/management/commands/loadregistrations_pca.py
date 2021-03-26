import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_demand_extrema
from alert.models import Registration, Section
from courses.models import Course, Department
from PennCourses.command_utils import get_num_lines


def load_pca_registrations(file_path, dummy_missing_sections=False):
    """
    :param file_path: Path to the csv specifying the registrations.
        The CSV for PCA registrations must have the following columns (one row per registration):
            dept code, course code, section code, semester, created_at, id,
            resubscribed_from_id, notification_sent, notification_sent_at
    :param dummy_missing_sections: Set to True to fill in missing sections with dummy info
        (only containing dept_code, course_code, section_code, and semester).
    """
    print(
        "This script is an atomic transaction, so the database will not be modified "
        "unless the entire script succeeds."
    )
    with transaction.atomic():
        print(f"Verifying {file_path} is a valid CSV for loading PCA registrations...")

        def load_fail_print(i, line):
            print(
                f"For the above reason, row {i} (1-indexed) of {file_path} is invalid:\n"
                f"{line.strip()}\n(Not necessarily helpful reminder: Columns must be: "
                "dept code, course code, section code, semester, created_at, id "
                "[, resubscribed_from_id])\n\n"
                "Invalid input; no registrations were added to the database.\n"
            )

        searched_for_sections = dict()

        registrations = []
        with open(file_path) as f:
            i = 0
            for line in tqdm(f, total=get_num_lines(file_path)):
                i += 1
                bits = line.strip().split(",")
                if len(bits) != 9:
                    print(f"\nRow found with {len(bits)} (!=9) columns.")
                    load_fail_print(i, line)
                    return False
                dept_code = bits[0].upper()
                course_code = bits[1]
                section_code = bits[2]
                semester = bits[3]
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
                if found_section is None and not dummy_missing_sections:
                    print("\n\n")
                    print(
                        f"Section {dept_code}-{course_code}-{section_code} from semester "
                        f"{semester} not found and dummy_missing_sections was not flagged."
                    )
                    load_fail_print(i, line)
                    return False
                try:
                    if semester[-1].upper() not in ["A", "B", "C"]:
                        raise ValueError()
                except Exception as e:
                    print("\n\n")
                    print(f"Semester {semester} is invalid.")
                    print(e)
                    load_fail_print(i, line)
                    return False
                exception = ""
                dt = None
                try:
                    dt = parse_datetime(bits[4])
                except Exception as e:
                    dt = None
                    exception = e
                if dt is None:
                    print("\n\n")
                    print(f"Datetime '{bits[4]}' could not be parsed to a datetime object.")
                    if exception != "":
                        print(exception)
                    load_fail_print(i, line)
                    return False
                try:
                    created_at = make_aware(dt)
                except ValueError:
                    created_at = dt
                try:
                    id = int(bits[5])
                except ValueError:
                    print("\n\n")
                    print(f"Id value '{bits[5]}' could not be parsed as an int.")
                    load_fail_print(i, line)
                    return False

                resubscribed_from_id = None
                if bits[6] != "":
                    try:
                        resubscribed_from_id = int(bits[6])
                    except ValueError:
                        print("\n\n")
                        print(
                            f"Resubscribed_from_id value '{bits[6]}' could not be parsed as an int."
                        )
                        load_fail_print(i, line)
                        return False
                try:
                    notification_sent = bool(int(bits[7]))
                except ValueError:
                    print("\n\n")
                    print(f"Notification_sent value '{bits[7]}' could not be parsed as a bool.")
                    load_fail_print(i, line)
                    return False
                notification_sent_at = None
                if notification_sent:
                    fail = False
                    dt = None
                    try:
                        dt = parse_datetime(bits[8])
                    except ValueError:
                        fail = True
                    if dt is None:
                        fail = True
                    if fail:
                        print("\n\n")
                        print(
                            f"Notification_sent_at value '{bits[8]}' could not be parsed as a "
                            "datetime."
                        )
                        load_fail_print(i, line)
                        return False
                    try:
                        notification_sent_at = make_aware(dt)
                    except ValueError:
                        notification_sent_at = dt

                if (
                    found_section is not None
                    and Registration.objects.filter(
                        section=found_section,
                        created_at=created_at,
                        notification_sent=notification_sent,
                        notification_sent_at=notification_sent_at,
                    ).exists()
                ):
                    print("\n\n")
                    print(
                        f"A registration with section {dept_code}-{course_code}-{section_code} "
                        f"{semester}, 'created_at'='{created_at}' and 'notification_sent_at'="
                        f"'{notification_sent_at}' already exists in database. Did you "
                        "accidentally run this script twice?"
                    )
                    load_fail_print(i, line)
                    return False

                registrations.append(
                    (
                        dept_code,
                        course_code,
                        section_code,
                        semester,
                        found_section,
                        created_at,
                        id,
                        resubscribed_from_id,
                        notification_sent,
                        notification_sent_at,
                    )
                )

        print("Verification succeeded! Proceeding to load registrations...")

        id_corrections = dict()
        num_dummy_sections = 0
        created_sections = dict()
        semesters = set()

        for tup in tqdm(registrations):
            (
                dept_code,
                course_code,
                section_code,
                semester,
                found_section,
                created_at,
                id,
                resubscribed_from_id,
                notification_sent,
                notification_sent_at,
            ) = tup

            if found_section is None:
                full_code = f"{dept_code}-{course_code}-{section_code}"
                if f"{full_code} {semester}" in created_sections:
                    section = created_sections[f"{full_code} {semester}"]
                else:
                    num_dummy_sections += 1
                    dept, _ = Department.objects.get_or_create(code=dept_code)
                    course, _ = Course.objects.get_or_create(
                        department=dept, code=course_code, semester=semester
                    )
                    section = Section(course=course, code=section_code, full_code=full_code)
                    section.save()
                    created_sections[f"{full_code} {semester}"] = section
            else:
                section = found_section

            semesters.add(section.semester)

            registration = Registration(section=section, source="SCRIPT_PCA")
            registration.save(load_script=True)
            registration.created_at = created_at
            registration.notification_sent = notification_sent
            if notification_sent:
                registration.notification_sent_at = notification_sent_at
            registration.save(load_script=False)
            id_corrections[id] = registration.id

        print("Connecting resubscribe chains...")

        for tup in tqdm(registrations):
            (_, _, _, _, _, _, id, resubscribed_from_id, _, _) = tup

            registration = Registration.objects.get(id=id_corrections[id], source="SCRIPT_PCA")
            if resubscribed_from_id is not None:
                registration.resubscribed_from = Registration.objects.get(
                    id=id_corrections[resubscribed_from_id], source="SCRIPT_PCA"
                )
            registration.save(load_script=True)

        print("Correcting original_created_at values...")
        for tup in tqdm(registrations):
            (_, _, _, _, _, _, id, _, _, _) = tup
            registration = Registration.objects.get(id=id_corrections[id], source="SCRIPT_PCA")
            registration.original_created_at = None
            registration.save(load_script=True)

        print(f"Recomputing PCA Demand Extrema for {len(semesters)} semesters...")
        for semester in semesters:
            recompute_demand_extrema(semesters=semester, verbose=True)

        print(
            f"Done! {len(registrations)} registrations and {num_dummy_sections} dummy sections "
            "added to database."
        )
        return True


class Command(BaseCommand):
    help = "Load in PCA registrations from a csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path", type=str, help="The path to the csv you want to load registrations from."
        )
        parser.add_argument(
            "--dummy_missing_sections",
            action="store_true",
            help=(
                "Flag to fill in missing sections with dummy info (only containing "
                "dept_code, course_code, section_code, and semester)"
            ),
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        src = os.path.abspath(kwargs["file_path"])
        _, file_extension = os.path.splitext(kwargs["file_path"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."
        print(f"Loading PCA registrations from path {src}")
        load_pca_registrations(
            file_path=src, dummy_missing_sections=kwargs["dummy_missing_sections"]
        )
