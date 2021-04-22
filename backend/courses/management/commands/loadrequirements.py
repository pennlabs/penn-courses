import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.models import Course, Department, Requirement
from courses.requirements import engineering, wharton
from courses.util import get_current_semester


def load_requirements(school=None, semester=None, requirements=None):
    """
    :param school: School to load requirements from. Current options are WH (Wharton) and
        SEAS (Engineering)
    :param semester: Semester to load requirements in for.
    :param requirements: If school is not specified, can input a custom requirements dict
    in this format:
    {
        codes: {"<requirement code>": "<full requirement name>", ...},
        data: [
            {
                "department": <department>,
                "course_id": <course id OR None if requirement is for whole course>},
                "satisfies": <False if describing a course override,
                              True for courses and depts which satisfy the req>
            },
            ... [one dict for every requirement rule]
        ]
    }
    """
    if semester is None:
        semester = get_current_semester()

    if school == "WH":
        requirements = wharton.get_requirements()
    elif school == "SEAS":
        requirements = engineering.get_requirements()
    elif requirements is None:
        return None

    codes = requirements["codes"]
    data = requirements["data"]

    for req_id, items in tqdm(data.items()):
        # if this isn't a requirement we define in codes, then don't update it.
        if req_id not in codes:
            continue
        requirement = Requirement.objects.get_or_create(
            semester=semester, school=school, code=req_id, defaults={"name": codes[req_id]}
        )[0]
        for item in items:
            dept_id = item.get("department")
            course_id = item.get("course_id")
            satisfies = item.get("satisfies")
            dept, _ = Department.objects.get_or_create(code=dept_id)
            if course_id is None:
                requirement.departments.add(dept)
            else:
                # Unlike most functionality with courses, we do not want to create a relation
                # between a course and a requirement if the course does not exist.
                try:
                    course = Course.objects.get(department=dept, code=course_id, semester=semester)
                except Course.DoesNotExist:
                    continue
                if satisfies:
                    requirement.courses.add(course)
                else:
                    requirement.overrides.add(course)


class Command(BaseCommand):
    help = "Load in courses, sections and associated models from the Penn registrar and requirements data sources."  # noqa: E501

    def add_arguments(self, parser):
        parser.add_argument("--semester", nargs="?", type=str)
        parser.add_argument("--school", nargs="?", default="")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        print(
            f'Loading requirements for school {kwargs["school"]} and semester {kwargs["semester"]}'
        )
        load_requirements(school=kwargs["school"], semester=kwargs["semester"])
