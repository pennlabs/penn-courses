import redis
import logging

from django.conf import settings
from celery import shared_task

from options.models import get_value, get_bool
from . import registrar
from .util import upsert_course_from_opendata, get_course
from .models import Course, Requirement

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
        requirements = wharton.get_wharton_requirements()
    else:
        return None

    codes = requirements['codes']
    data = requirements['data']

    rcache = {}

    def get_req(r):
        if r in rcache:
            return rcache[r]
        else:
            rcache[r] = Requirement.objects.get_or_create(semester=semester,
                                                          school=school,
                                                          satisfies=True,
                                                          code=r,
                                                          defaults={
                                                            'name': codes.get(r, '')
                                                          })[0]
            return rcache[r]

    for line in data:
        course = get_course(line['department'], line['course_id'], semester)
        for req in line['requirements']:
            requirement = get_req(req)
            requirement.courses.add(course)



