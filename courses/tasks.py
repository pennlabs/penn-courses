import logging

from celery import shared_task

from courses import registrar
from courses.models import Course, Department, Requirement
from courses.util import upsert_course_from_opendata
from options.models import get_value


logger = logging.getLogger(__name__)


@shared_task(name='courses.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.setLevel(logging.DEBUG)
    print('load in courses with prefix %s from %s' % (query, semester))
    results = registrar.get_courses(query, semester)

    num_courses = len(results)
    i = 0
    for course in results:
        if i % 100 == 0:
            print(f'loading in course {i} / {num_courses}')
        upsert_course_from_opendata(course, semester)
        i += 1

    return {'result': 'succeeded', 'name': 'courses.tasks.load_courses'}


def load_requirements(school=None, semester=None, requirements=None):
    """
    :param school: School to load requirements from. Current options are WH (Wharton) and SEAS (Engineering)
    :param semester: Semester to load requirements in for.
    :param requirements: If school is not specified, can input a custom requirements dict in this format:
    {
        codes: {"<requirement code>": "<full requirement name>", ...},
        data: [
            {
                "department": <department>,
                "course_id": <course id OR None if requirement is for whole course>},
                "satisfies": <False if describing a course override, True for courses and depts which satisfy the req>
            },
            ... [one dict for every requirement rule]
        ]
    }
    """
    if semester is None:
        semester = get_value('SEMESTER')

    if school == 'WH':
        from .requirements import wharton
        requirements = wharton.get_requirements()
    elif school == 'SEAS':
        from .requirements import engineering
        requirements = engineering.get_requirements()
    elif requirements is None:
        return None

    codes = requirements['codes']
    data = requirements['data']

    for req_id, items in data.items():
        # if this isn't a requirement we define in codes, then don't update it.
        if req_id not in codes:
            continue
        requirement = Requirement.objects.get_or_create(semester=semester,
                                                        school=school,
                                                        code=req_id,
                                                        defaults={
                                                          'name': codes[req_id]
                                                        })[0]
        for item in items:
            dept_id = item.get('department')
            course_id = item.get('course_id')
            satisfies = item.get('satisfies')
            dept, _ = Department.objects.get_or_create(code=dept_id)
            if course_id is None:
                requirement.departments.add(dept)
            else:
                # Unlike most functionality with courses, we do not want to create a relation between a course
                # and a requirement if the course does not exist.
                try:
                    course = Course.objects.get(department=dept, code=course_id, semester=semester)
                except Course.DoesNotExist:
                    continue
                if satisfies:
                    requirement.courses.add(course)
                else:
                    requirement.overrides.add(course)


@shared_task(name='courses.tasks.semester_sync')
def semester_sync(query='', semester=None):
    load_courses(query=query, semester=semester)
    load_requirements(school='SEAS', semester=semester)
    load_requirements(school='WH', semester=semester)
