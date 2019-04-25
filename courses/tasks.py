import redis
import logging

from django.conf import settings
from celery import shared_task

from options.models import get_value, get_bool
from . import registrar
from .util import upsert_course_from_opendata

logger = logging.getLogger(__name__)
r = redis.Redis.from_url(settings.REDIS_URL)


@shared_task(name='pca.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.info('load in courses with prefix %s from %s' % (query, semester))
    results = registrar.get_courses(query, semester)

    for course in results:
        upsert_course_from_opendata(course, semester)

    return {'result': 'succeeded', 'name': 'pca.tasks.load_courses'}