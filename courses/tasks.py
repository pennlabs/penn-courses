import redis
import logging

from django.conf import settings
from celery import shared_task

from options.models import get_value, get_bool
from . import registrar
from .util import upsert_course_from_opendata, get_course
from .models import Course, Requirement, Department

logger = logging.getLogger(__name__)


# @shared_task(name='courses.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.info('load in courses with prefix %s from %s' % (query, semester))
    results = registrar.get_courses(query, semester)

    for course in results:
        upsert_course_from_opendata(course, semester)

    return {'result': 'succeeded', 'name': 'courses.tasks.load_courses'}


def load_requirements(school=None, semester=None, requirements=None):
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
        requirement = Requirement.objects.get_or_create(semester=semester,
                                                        school=school,
                                                        code=req_id,
                                                        defaults={
                                                          'name': codes.get(req_id, '')
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
