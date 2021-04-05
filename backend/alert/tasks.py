import logging
from contextlib import nullcontext

import redis
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from alert.models import AddDropPeriod, PcaDemandExtrema, Registration
from courses.models import Section, StatusUpdate
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
        return list(section.registrations.filter(**Registration.is_active_filter()))
    elif course_status == "C":
        # Use the is_waiting_for_close_filter dict statically defined in the Registration model
        return list(section.registrations.filter(*Registration.is_waiting_for_close_filter()))
    else:
        return []


@shared_task(name="pca.tasks.send_course_alerts")
def send_course_alerts(course_code, course_status, semester=None, sent_by=""):
    if semester is None:
        semester = get_current_semester()

    for reg in get_registrations_for_alerts(course_code, semester, course_status=course_status):
        send_alert.delay(reg.id, close_notification=(course_status == "C"), sent_by=sent_by)


@shared_task(name="pca.tasks.registration_update")
def registration_update(section_id, was_active, is_now_active, updated_at):
    """
    This method should only be called on sections from the current semester. It updates the
    registration_volume of the registration's section, it updates the PcaDemandExtrema
    models and current_demand_extrema cache to reflect the demand change.
    """
    section = Section.objects.get(id=section_id)
    semester = section.semester
    add_drop_period = AddDropPeriod.objects.get(semester=semester)
    assert semester == get_current_semester()
    if was_active == is_now_active:
        return
    volume_change = int(is_now_active) - int(was_active)
    if volume_change < 0:
        if section.registration_volume is None:
            section.registration_volume = 0
            section.save()
        elif section.registration_volume >= 1:
            section.registration_volume += volume_change
            section.save()
    else:
        if section.registration_volume is None:
            section.registration_volume = 0
        section.registration_volume += volume_change
        section.save()

    cache_context = (
        cache.lock("current_demand_extrema") if hasattr(cache, "lock") else nullcontext()
    )
    with transaction.atomic(), cache_context:
        sentinel = object()
        current_demand_extrema = cache.get("current_demand_extrema", sentinel)
        if current_demand_extrema == sentinel or current_demand_extrema["semester"] != semester:
            try:
                latest_extrema_ob = (
                    PcaDemandExtrema.objects.filter(semester=semester)
                    .select_for_update()
                    .latest("created_at")
                )
                current_demand_extrema = latest_extrema_ob
            except PcaDemandExtrema.DoesNotExist:
                current_demand_extrema = None

        if current_demand_extrema is None:
            if section.capacity is not None and section.capacity > 0:
                pca_demand_extrema = PcaDemandExtrema(
                    created_at=updated_at,
                    semester=semester,
                    most_popular_section=section,
                    most_popular_volume=section.registration_volume,
                    least_popular_section=section,
                    least_popular_volume=section.registration_volume,
                )
                pca_demand_extrema.save(add_drop_period=add_drop_period)
            return

        new_max = section.raw_demand > current_demand_extrema.highest_raw_demand
        if new_max:
            most_popular_section = section
        new_min = section.raw_demand < current_demand_extrema.lowest_raw_demand
        if new_min:
            least_popular_section = section
        new_extrema = new_min or new_max
        if volume_change < 0 and section == current_demand_extrema.most_popular_section:
            most_popular_section = (
                Section.objects.filter(semester=semester)
                .select_for_update()
                .order_by("-raw_demand")
                .first()
            )
            if most_popular_section != section:
                new_extrema = True
                new_max = True
        if volume_change > 0 and section == current_demand_extrema.least_popular_section:
            least_popular_section = (
                Section.objects.filter(semester=semester)
                .select_for_update()
                .order_by("raw_demand")
                .first()
            )
            if least_popular_section != section:
                new_extrema = True
                new_min = True

        if new_extrema:
            new_demand_extrema = PcaDemandExtrema(
                created_at=updated_at,
                semester=semester,
                most_popular_section=most_popular_section
                if new_max
                else current_demand_extrema.most_popular_section,
                most_popular_volume=most_popular_section.registration_volume
                if new_max
                else current_demand_extrema.most_popular_volume,
                least_popular_section=least_popular_section
                if new_min
                else current_demand_extrema.least_popular_section,
                least_popular_volume=least_popular_section.registration_volume
                if new_min
                else current_demand_extrema.least_popular_volume,
            )
            new_demand_extrema.save()
            cache.set("current_demand_extrema", new_demand_extrema, timeout=None)
