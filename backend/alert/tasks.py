import logging
from datetime import datetime

import numpy as np
import redis
import scipy.stats as stats
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Case, Max, Min, Q, When
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
from PennCourses.settings.base import (
    DEMAND_RECOMPUTE_DEBOUNCE_SECONDS,
    ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES,
)
from review.views import extra_metrics_section_filters


logger = logging.getLogger(__name__)
r = redis.Redis.from_url(settings.REDIS_URL)
DEMAND_RECOMPUTE_SCHEDULED_KEY = "demand_distribution_recompute_scheduled"


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


def schedule_demand_recompute(section, updated_at, delay=DEMAND_RECOMPUTE_DEBOUNCE_SECONDS):
    """
    Schedules a `section_demand_change` recompute, debouncing so that a burst of demand changes
    (e.g. the many status updates `sync_path_status` can emit in one run) coalesces into a single
    recompute. The estimate is a semester-wide aggregate, so recomputing it per section is
    duplicated work.

    `cache.add` is atomic, so only the first caller in a window enqueues. `section_demand_change`
    clears the key when it starts, so changes arriving mid-recompute schedule a fresh one --
    updates are coalesced, never dropped. The enqueued task carries the `updated_at` of the
    *first* change in the window, so the estimate's `created_at` may be up to `delay` seconds early.

    :param: section: the section involved in the demand change
    :param: updated_at: the datetime at which the demand change occurred
    :param: delay: how long to wait (and coalesce changes) before recomputing, in seconds
    """
    # `section_demand_change` only estimates for the current semester, so a past-semester caller
    # must not take the window -- it would suppress current-semester changes and then no-op.
    if section.semester != get_current_semester():
        return
    # Timeout exceeds the countdown so a task lost before it runs can't wedge the key.
    scheduled = cache.add(DEMAND_RECOMPUTE_SCHEDULED_KEY, "1", timeout=delay + 60)
    if scheduled is False:
        return  # Already scheduled for this window
    # `add` returns None if the cache backend is down (IGNORE_EXCEPTIONS in prod); fail open.
    section_demand_change.apply_async((section.id, updated_at), countdown=delay)


def sections_with_raw_demand(semester):
    """
    Returns a queryset of the sections in the given semester which count towards the demand
    distribution estimate, annotated with their `raw_demand` (registration volume over capacity).
    """
    return Section.objects.filter(
        extra_metrics_section_filters, course__semester=semester
    ).annotate(
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


def needs_new_estimate(current_estimate, semester, sections_qs):
    """
    Returns whether the sections in `sections_qs` have moved outside the demand range covered by
    `current_estimate` (or whether there is no usable estimate for `semester` at all), meaning a
    new `PcaDemandDistributionEstimate` should be computed.

    One aggregate pass, replacing the two `ORDER BY raw_demand LIMIT 1` queries the old
    implementation ran up-front. `raw_demand` is a computed expression, so those were full sorts
    over the semester, paid on every call even though most calls don't move the extrema.
    """
    extrema = sections_qs.aggregate(
        max_raw_demand=Max("raw_demand"), min_raw_demand=Min("raw_demand")
    )
    if extrema["max_raw_demand"] is None or extrema["min_raw_demand"] is None:
        return False  # No valid sections yet, so there's nothing to estimate from
    if current_estimate is None or current_estimate.semester != semester:
        return True
    highest = current_estimate.highest_raw_demand
    lowest = current_estimate.lowest_raw_demand
    if highest is None or lowest is None:
        return True  # The estimate references a section we can no longer derive demand from
    return extrema["max_raw_demand"] > highest or extrema["min_raw_demand"] < lowest


@shared_task(name="pca.tasks.registration_update")
def section_demand_change(section_id, updated_at):
    """
    This function should be called when a section's demand changes (i.e. the number of
    active registrations changes, or the section's status is updated). It updates the
    `PcaDemandDistributionEstimate` model and `current_demand_distribution_estimate`
    cache to reflect the demand change.

    Prefer scheduling this via `schedule_demand_recompute` rather than calling it directly, so
    bursts of demand changes are coalesced into a single recompute.

    :param: section_id: the id of the section involved in the demand change
    :param: updated_at: the datetime at which the demand change occurred
    """
    # Reopen the debounce window now, so changes landing mid-recompute schedule a follow-up.
    cache.delete(DEMAND_RECOMPUTE_SCHEDULED_KEY)

    if type(updated_at) is str:
        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    elif type(updated_at) is not datetime:
        return

    section = Section.objects.get(id=section_id)
    semester = section.semester
    if semester != get_current_semester():
        return

    current_demand_distribution_estimate = cache.get("current_demand_distribution_estimate")
    sections_qs = sections_with_raw_demand(semester)

    # Lock-free pre-check: in the common case nothing has moved, and we take no locks at all.
    if not needs_new_estimate(current_demand_distribution_estimate, semester, sections_qs):
        return

    with transaction.atomic():
        # Only rows read inside the transaction are locked, so re-derive the queryset here.
        locked_sections_qs = sections_qs.select_for_update()

        try:
            lowest_demand_section = locked_sections_qs.order_by("raw_demand")[:1].get()
            highest_demand_section = locked_sections_qs.order_by("-raw_demand")[:1].get()
        except Section.DoesNotExist:
            return  # Don't add a PcaDemandDistributionEstimate -- there are no valid sections yet

        closed_sections_demand_values = np.asarray(
            locked_sections_qs.filter(status="C").values_list("raw_demand", flat=True)
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
