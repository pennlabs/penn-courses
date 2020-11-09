import logging

import redis
from celery import shared_task
from django.conf import settings

from alert.models import Registration
from courses.models import StatusUpdate
from courses.util import get_course_and_section, get_current_semester, update_course_from_record


logger = logging.getLogger(__name__)
r = redis.Redis.from_url(settings.REDIS_URL)


@shared_task(name="pca.tasks.run_course_updates")
def run_course_updates(semester=None):
    if semester is None:
        updates = StatusUpdate.objects.all()
    else:
        updates = StatusUpdate.objects.filter(section__course__semester=semester)
    for u in updates:
        update_course_from_record(u)
    return {"result": "executed", "name": "pca.tasks.run_course_updates"}


@shared_task(name="pca.tasks.send_alert")
def send_alert(reg_id, sent_by=""):
    result = Registration.objects.get(id=reg_id).alert(sent_by=sent_by)
    return {"result": result, "task": "pca.tasks.send_alert"}


def get_active_registrations(course_code, semester):
    _, section = get_course_and_section(course_code, semester)
    # Use the is_active filters statically defined in the Registration model
    return list(section.registration_set.filter(**Registration.is_active_filter()))


def get_registrations_for_alerts(course_code, semester, course_status="O"):
    _, section = get_course_and_section(course_code, semester)
    if course_status == "O":
        # Use the is_active filters statically defined in the Registration model
        return get_active_registrations(course_code, semester)
    else:
        # Use the is_waiting_for_close_filter filters statically defined in the Registration model
        return list(section.registration_set.filter(**Registration.is_waiting_for_close_filter()))


@shared_task(name="pca.tasks.send_course_alerts")
def send_course_alerts(course_code, semester=None, sent_by="", course_status="O"):
    if semester is None:
        semester = get_current_semester()

    for reg in get_registrations_for_alerts(course_code, semester, course_status=course_status):
        send_alert.delay(reg.id, sent_by)
