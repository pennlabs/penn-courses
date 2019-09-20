import redis
import json
import logging
from celery import shared_task

from .models import *

from options.models import get_value, get_bool

from django.conf import settings

logger = logging.getLogger(__name__)
r = redis.Redis.from_url(settings.REDIS_URL)


def generate_course_json(semester=None, use_cache=True):
    if semester is None:
        semester = get_value('SEMESTER')

    if use_cache:
        sections = r.get('sections')
        if sections is not None:
            return json.loads(sections)

    sections = []
    for section in Section.objects.filter(course__semester=semester):
        # {'section_id': section_id, 'course_title': course_title, 'instructors': instructors,
        #  'meeting_days': meeting_days}
        # meetings = json.loads('{"meetings": "%s"}' % section.meeting_times)['meetings']
        if section.meeting_times is not None and len(section.meeting_times) > 0:
            meetings = json.loads(section.meeting_times)
        else:
            meetings = []
        sections.append({
            'section_id': section.normalized,
            'course_title': section.course.title,
            'instructors': list(map(lambda i: i.name, section.instructors.all())),
            'meeting_days': meetings
        })

    serialized_sections = json.dumps(sections)
    r.set('sections', serialized_sections)
    return sections


@shared_task(name='pca.tasks.update_course_json')
def update_course_json():
    generate_course_json(use_cache=False)


@shared_task(name='pca.tasks.demo_alert')
def demo_alert():
    return {'result': 'executed', 'name': 'pca.tasks.demo_alert'}


@shared_task(name='pca.tasks.demo_task')
def demo_task():
    return {'result': 'executed', 'name': 'pca.tasks.demo_task'}


@shared_task(name='pca.tasks.run_course_updates')
def run_course_updates(semester=None):
    if semester is None:
        updates = CourseUpdate.objects.all()
    else:
        updates = CourseUpdate.objects.filter(section__course__semester=semester)
    for u in updates:
        update_course_from_record(u)
    return {'result': 'executed', 'name': 'pca.tasks.run_course_updates'}


@shared_task(name='pca.tasks.send_alert')
def send_alert(reg_id, sent_by=''):
    result = Registration.objects.get(id=reg_id).alert(sent_by=sent_by)
    return {
        'result': result,
        'task': 'pca.tasks.send_alert'
    }


def get_active_registrations(course_code, semester):
    _, section = get_course_and_section(course_code, semester)
    return list(section.registration_set.filter(notification_sent=False))


@shared_task(name='pca.tasks.send_course_alerts')
def send_course_alerts(course_code, semester=None, sent_by=''):
    if semester is None:
        semester = get_value('SEMESTER')

    for reg in get_active_registrations(course_code, semester):
        send_alert.delay(reg.id, sent_by)
