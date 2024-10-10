import logging
from datetime import datetime

import numpy as np
import redis
import scipy.stats as stats
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Case, Q, When
from django.db.models.functions import Cast

from alert.models import PcaDemandDistributionEstimate, Registration
from courses.management.commands.recompute_soft_state import recompute_percent_open
from courses.models import Section, StatusUpdate
from courses.util import (
    get_course_and_section,
    get_current_semester,
    get_or_create_add_drop_period,
    update_course_from_record,
)
from PennCourses.settings.base import ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES
from review.views import extra_metrics_section_filters


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
        return list(section.registrations.filter(**Registration.is_active_filter()))
    elif course_status == "C":
        return list(section.registrations.filter(**Registration.is_waiting_for_close_filter()))
    else:
        return []


@shared_task(name="pca.tasks.send_course_alerts")
def send_course_alerts(course_code, course_status, semester=None, sent_by=""):
    if semester is None:
        semester = get_current_semester()

    for reg in get_registrations_for_alerts(course_code, semester, course_status=course_status):
        send_alert.delay(reg.id, close_notification=(course_status == "C"), sent_by=sent_by)


@shared_task(name="pca.tasks.recompute_percent_open")
def recompute_percent_open_async(semester):
    recompute_percent_open(semesters=[semester])


@shared_task(name="pca.tasks.registration_update")
def section_demand_change(section_id, updated_at):
    """
    This function should be called when a section's demand changes (i.e. the number of
    active registrations changes, or the section's status is updated). It updates the
    `PcaDemandDistributionEstimate` model and `current_demand_distribution_estimate`
    cache to reflect the demand change.

    :param: section_id: the id of the section involved in the demand change
    :param: updated_at: the datetime at which the demand change occurred
    """
    if type(updated_at) is str:
        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    elif type(updated_at) is not datetime:
        return

    section = Section.objects.get(id=section_id)
    semester = section.semester
    if semester != get_current_semester():
        return

    with transaction.atomic():
        create_new_distribution_estimate = False
        sentinel = object()
        current_demand_distribution_estimate = cache.get(
            "current_demand_distribution_estimate", sentinel
        )
        if (
            current_demand_distribution_estimate == sentinel
            or current_demand_distribution_estimate.semester != semester
        ):
            create_new_distribution_estimate = True

        sections_qs = (
            Section.objects.filter(extra_metrics_section_filters, course__semester=semester)
            .select_for_update()
            .annotate(
                raw_demand=Case(
                    When(
                        Q(capacity__gt=0),
                        then=(
                            Cast(
                                "registration_volume",
                                models.FloatField(),
                            )
                            / Cast("capacity", models.FloatField())
                        ),
                    ),
                    default=None,
                    output_field=models.FloatField(),
                ),
            )
        )

        try:
            lowest_demand_section = sections_qs.order_by("raw_demand")[:1].get()
            highest_demand_section = sections_qs.order_by("-raw_demand")[:1].get()
        except Section.DoesNotExist:
            return  # Don't add a PcaDemandDistributionEstimate -- there are no valid sections yet

        if (
            create_new_distribution_estimate
            or highest_demand_section.raw_demand
            > current_demand_distribution_estimate.highest_raw_demand
            or lowest_demand_section.raw_demand
            < current_demand_distribution_estimate.lowest_raw_demand
        ):
            closed_sections_demand_values = np.asarray(
                sections_qs.filter(status="C").values_list("raw_demand", flat=True)
            )
            # "The term 'closed sections positive raw demand values' is
            # sometimes abbreviated as 'csprdv'
            csrdv_frac_zero, fit_shape, fit_loc, fit_scale = (None, None, None, None)
            if len(closed_sections_demand_values) > 0:
                closed_sections_positive_demand_values = closed_sections_demand_values[
                    np.where(closed_sections_demand_values > 0)
                ]
                csrdv_frac_zero = 1 - len(closed_sections_positive_demand_values) / len(
                    closed_sections_demand_values
                )
                if len(closed_sections_positive_demand_values) > 0:
                    fit_shape, fit_loc, fit_scale = stats.lognorm.fit(
                        closed_sections_positive_demand_values
                    )
            new_demand_distribution_estimate = PcaDemandDistributionEstimate(
                semester=semester,
                highest_demand_section=highest_demand_section,
                highest_demand_section_volume=highest_demand_section.registration_volume,
                lowest_demand_section=lowest_demand_section,
                lowest_demand_section_volume=lowest_demand_section.registration_volume,
                csrdv_frac_zero=csrdv_frac_zero,
                csprdv_lognorm_param_shape=fit_shape,
                csprdv_lognorm_param_loc=fit_loc,
                csprdv_lognorm_param_scale=fit_scale,
            )
            add_drop_period = get_or_create_add_drop_period(semester)
            new_demand_distribution_estimate.save(add_drop_period=add_drop_period)
            new_demand_distribution_estimate.created_at = updated_at
            new_demand_distribution_estimate.save(add_drop_period=add_drop_period)
            cache.set(
                "current_demand_distribution_estimate",
                new_demand_distribution_estimate,
                timeout=(
                    add_drop_period.estimated_end - add_drop_period.estimated_start
                ).total_seconds()
                // ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES,
            )  # set timeout to roughly follow ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES
