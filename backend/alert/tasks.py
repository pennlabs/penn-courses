import logging

import redis
from celery import shared_task
from django.conf import settings
from options.models import get_value

from alert.models import Registration
from courses.models import StatusUpdate
from courses.util import get_course_and_section, update_course_from_record


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


def get_active_registrations(course_code, semester, course_status="O"):
    _, section = get_course_and_section(course_code, semester)
    # if open then want registrations where the notification has not yet been sent else closed and then want where notification has been sent and where user has requested a close notification
    if course_status == "O": 
        return list(section.registration_set.filter(notification_sent=False, deleted=False))
    else:
        return list(section.registration_set.filter(close_notification=True, notification_sent=True, deleted=False))


@shared_task(name="pca.tasks.send_course_alerts")
def send_course_alerts(course_code, semester=None, sent_by="", course_status="O"):
    if semester is None:
        semester = get_value("SEMESTER")

    for reg in get_active_registrations(course_code, semester, course_status=course_status):
        send_alert.delay(reg.id, sent_by)
