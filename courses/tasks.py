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


def load_requirements(school, semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    if school == 'WH':
        from .requirements import wharton
        requirements = wharton.get_requirements()
    else:
        return None

    codes = requirements['codes']
    data = requirements['data']

    for req_id, items in data.items():
        requirement = Requirement.objects.get_or_create(semester=semester,
                                                        school=school,
                                                        satisfies=True,
                                                        code=req_id,
                                                        defaults={
                                                          'name': codes.get(req_id, '')
                                                        })[0]
        for item in items:
            dept_id = item.get('dept_id')
            course_id = item.get('course_id')
            satisfies = item.get('satisfies')
            dept, _ = Department.objects.get_or_create(code=dept_id)
            if course_id is None:
                requirement.departments.add(dept)
            else:
                # TODO: Maybe don't just get or create the course? Only add it as a requirement if it already exists?
                # Since not every course is offered every semester.
                try:
                    course = Course.objects.get(department=dept, code=course_id, semester=semester)
                except Course.DoesNotExist:
                    continue
                if satisfies:
                    requirement.courses.add(course)
                else:
                    requirement.overrides.add(course)
