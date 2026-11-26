import json
import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from alert.models import Course, Section
from courses import registrar
from courses.util import get_course_and_section, get_current_semester, translate_semester_inv


class Command(BaseCommand):
    help = """
        Generate an audit report that demonstrates the differences between our
        database and the course statuses received from using the OpenData
        endpoint directly.

        Note that this script DOES NOT make any changes to the database, just
        generates a textfile report
    """

    def handle(self, *args, **options):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        semester = get_current_semester()
        statuses = registrar.get_all_course_status(semester)
        stats = {
            "missing_data": 0,
            "section_not_found": 0,
            "duplicate_updates": 0,
            "unsynced_updates": 0,
        }
        unsynced_courses = []
        for status in tqdm(statuses):
            data = status
            section_code = data.get("section_id_normalized")
            if section_code is None:
                stats["missing_data"] += 1
                continue

            course_status = data.get("status")
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
            current_status = section.status
            if current_status == course_status:
                stats["duplicate_updates"] += 1
                continue

            stats["unsynced_updates"] += 1
            unsynced_courses.append(
                (section_code, last_status_update.new_status, current_status, course_status)
            )

        # Write out statistics and missing courses to an output file.
        with open("./status_audit.txt", "w") as f:
            f.write("Summary Statistics\n")
            f.write(json.dumps(stats) + "\n\n")

            f.write(
                """Courses Out of Sync\nCourse Code / Last Update Status /
                 Our Stored Status / Actual Status\n"""
            )
            f.write("Our Status Matches Last Update\n")
            f.writelines(
                [
                    f"{course[0]} / {course[1]} / {course[2]} / {course[3]}\n"
                    for course in unsynced_courses
                    if course[1] == course[2]
                ]
            )

            f.write("\nOur Status Does Not Match Last Update\n")
            f.writelines(
                [
                    f"{course[0]} / {course[1]} / {course[2]} / {course[3]}\n"
                    for course in unsynced_courses
                    if course[1] != course[2]
                ]
            )
