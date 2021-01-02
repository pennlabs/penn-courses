import logging
import mmap
import os

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from tqdm import tqdm

from alert.models import Registration, Section
from courses.models import Course, Department


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


def load_pca_registrations(file_path, dummy_missing_sections=False):
    """
    :param file_path: Path to the csv specifying the registrations.
        The CSV for PCA registrations must have the following columns (one row per registration):
            dept code, course code, section code, semester, created_at, id [, resubscribed_from_id]
    :param dummy_missing_sections: Set to True to fill in missing sections with dummy info
        (only containing dept_code, course_code, section_code, and semester).
    """
    print(
        f"Verifying {file_path} is a valid CSV for loading PCA registrations (nothing will be "
        "added to the database until indicated later)..."
    )

    def load_fail_print(i, line):
        print(
            f"Row {i} (1-indexed) of {file_path} is invalid:\n{line.strip()}\n"
            f"Columns must be: dept code, course code, section code, semester, "
            "created_at, id [, resubscribed_from_id]\n\n"
            "Invalid input; no registrations were added to the database.\n"
        )

    searched_for_sections = dict()

    registrations = []
    with open(file_path) as f:
        i = 0
        for line in tqdm(f, total=get_num_lines(file_path)):
            i += 1
            bits = line.strip().split(",")
            if len(bits) < 6:
                print(f"\nRow found with {len(bits)} (<6) columns.")
                load_fail_print(i, line)
                return False
            if len(bits) > 7:
                print(f"\nRow found with {len(bits)} (>7) columns.")
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
                print(
                    f"\nSection {dept_code}-{course_code}-{section_code} from semester {semester} "
                    f"not found and dummy_missing_sections was not flagged."
                )
                load_fail_print(i, line)
                return False
            try:
                if semester[-1].upper() not in ["A", "B", "C"]:
                    raise ValueError()
            except ValueError:
                print(f"\nSemester {semester} is invalid.")
                load_fail_print(i, line)
                return False
            exception = ""
            try:
                created_at = make_aware(parse_datetime(bits[4]))
            except Exception as e:
                created_at = None
                exception = e
            if created_at is None:
                print(f"\nDatetime '{bits[4]}' could not be parsed to a datetime object.")
                if exception != "":
                    print(exception)
                load_fail_print(i, line)
                return False
            try:
                id = int(bits[5])
            except ValueError:
                print(f"\nId value '{bits[5]}' could not be parsed as an int.")
                load_fail_print(i, line)
                return False

            resubscribed_from_id = None
            if len(bits) == 7 and bits[6] != "":
                try:
                    resubscribed_from_id = int(bits[6])
                except ValueError:
                    print(
                        f"\nResubscribed_from_id value '{bits[6]}' could not be parsed "
                        "as an int."
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
                )
            )

    print("Verification succeeded! Proceeding to load registrations (adding to database)...")

    class injection_dict(dict):
        """
        If a specified key has not yet been set, an injection_dict returns the key.
        """

        def __missing__(self, key):
            return key

    id_corrections = injection_dict()

    num_dummy_sections = 0

    created_sections = dict()

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

        correction = False
        if Registration.objects.filter(id=id).exists():
            registration = Registration(section=section)
            correction = True
        else:
            registration = Registration(section=section, id=id)
        registration.save()
        registration.created_at = created_at
        registration.save()
        if correction:
            id_corrections[id] = registration.id

    print("Connecting resubscribe chains...")

    for tup in tqdm(registrations):
        (dept_code, course_code, section_code, semester, created_at, id, resubscribed_from_id) = tup

        registration = Registration.objects.get(id=id_corrections[id])
        if resubscribed_from_id is not None:
            registration.resubscribed_from = Registration.objects.get(
                id=id_corrections[resubscribed_from_id]
            )
        registration.save()

    print("Correcting original_created_at values...")
    for tup in tqdm(registrations):
        (_, _, _, _, _, id, _) = tup
        registration = Registration.objects.get(id=id_corrections[id])
        registration.original_created_at = None
        registration.save()

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
