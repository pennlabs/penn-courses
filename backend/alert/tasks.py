import logging

import numpy as np
import redis
import scipy.stats as stats
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from alert.models import PcaDemandDistributionEstimate, Registration
from courses.models import Section, StatusUpdate
from courses.util import (
    get_add_drop_period,
    get_course_and_section,
    get_current_semester,
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


@shared_task(name="pca.tasks.registration_update")
def registration_update(section_id, was_active, is_now_active, updated_at):
    """
    This method should only be called on sections from the current semester. It updates the
    registration_volume of the registration's section, it updates the PcaDemandDistributionEstimate
    models and current_demand_distribution_estimate cache to reflect the demand change.
    """
    section = Section.objects.get(id=section_id)
    semester = section.semester
    assert (
        semester == get_current_semester()
    ), "Error: PCA registration from past semester cannot be updated."
    if was_active == is_now_active:
        # No change to registration volume
        return
    volume_change = int(is_now_active) - int(was_active)
    if volume_change < 0:
        if section.registration_volume >= 1:
            section.registration_volume += volume_change
            section.save()
    else:  # volume_change > 0
        section.registration_volume += volume_change
        section.save()

    with transaction.atomic():
        create_new_distribution_estimate = False
        sentinel = object()
        current_demand_distribution_estimate = cache.get(
            "current_demand_distribution_estimate", sentinel
        )
        if (
            current_demand_distribution_estimate == sentinel
            or current_demand_distribution_estimate["semester"] != semester
        ):
            create_new_distribution_estimate = True

        sections_qs = (
            Section.objects.filter(extra_metrics_section_filters, course__semester=semester)
            .distinct()
            .select_for_update()
            .order_by("raw_demand")
        )

        try:
            highest_demand_section = sections_qs.last()
            lowest_demand_section = sections_qs.first()
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
            # "The term 'closed sections demand values' is sometimes abbreviated as 'csdv'
            csdv_nonempty = len(closed_sections_demand_values) > 0
            fit_alpha, fit_loc, fit_scale, mean_log_likelihood = (None, None, None, None)
            if csdv_nonempty:
                fit_alpha, fit_loc, fit_scale = stats.gamma.fit(closed_sections_demand_values)
                mean_log_likelihood = stats.gamma.logpdf(
                    closed_sections_demand_values, fit_alpha, fit_loc, fit_scale
                ).mean()
            new_demand_distribution_estimate = PcaDemandDistributionEstimate(
                semester=semester,
                highest_demand_section=highest_demand_section,
                highest_demand_section_volume=highest_demand_section.registration_volume,
                lowest_demand_section=lowest_demand_section,
                lowest_demand_section_volume=lowest_demand_section.registration_volume,
                csdv_gamma_param_alpha=fit_alpha,
                csdv_gamma_param_loc=fit_loc,
                csdv_gamma_param_scale=fit_scale,
                csdv_gamma_fit_mean_log_likelihood=mean_log_likelihood,
                csdv_mean=(np.mean(closed_sections_demand_values) if csdv_nonempty else None),
                csdv_median=(np.median(closed_sections_demand_values) if csdv_nonempty else None),
                csdv_75th_percentile=(
                    np.percentile(closed_sections_demand_values, 75) if csdv_nonempty else None
                ),
            )
            add_drop_period = get_add_drop_period(semester)
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
