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
def send_alert(reg_id, close_notification, sent_by=""):
    result = Registration.objects.get(id=reg_id).alert(
        sent_by=sent_by, close_notification=close_notification
    )
    return {"result": result, "task": "pca.tasks.send_alert"}


def get_registrations_for_alerts(course_code, semester, course_status="O"):
    _, section = get_course_and_section(course_code, semester)
    if course_status == "O":
        # Use the is_active_filter dict statically defined in the Registration model
        return list(section.registration_set.filter(**Registration.is_active_filter()))
    elif course_status == "C":
        # Use the is_waiting_for_close_filter dict statically defined in the Registration model
        return list(section.registration_set.filter(**Registration.is_waiting_for_close_filter()))
    else:
        return []


@shared_task(name="pca.tasks.send_course_alerts")
def send_course_alerts(course_code, course_status, semester=None, sent_by=""):
    if semester is None:
        semester = get_current_semester()

    for reg in get_registrations_for_alerts(course_code, semester, course_status=course_status):
        send_alert.delay(reg.id, close_notification=(course_status == "C"), sent_by=sent_by)
