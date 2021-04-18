import logging
from contextlib import nullcontext
from textwrap import dedent

import numpy as np
import scipy.stats as stats
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from options.models import Option
from tqdm import tqdm

from alert.models import PcaDemandDistributionEstimate, Registration, Section
from courses.management.commands.load_add_drop_dates import load_add_drop_dates
from courses.models import Course, Restriction, StatusUpdate
from courses.util import get_add_drop_period, get_current_semester
from PennCourses.settings.base import (
    ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES,
    WAITLIST_DEPARTMENT_CODES,
)
from review.models import Review


def get_semesters(semesters=None, verbose=False):
    """
    Validate a given string semesters argument, and return a list of the individual string semesters
    specified by the argument.
    """
    possible_semesters = set(Course.objects.values_list("semester", flat=True).distinct())
    current_semester = get_current_semester()
    if semesters is None:
        semesters = [current_semester]
    elif semesters == "all":
        semesters = list(possible_semesters)
    else:
        semesters = semesters.strip().split(",")
        for s in semesters:
            if s not in possible_semesters:
                raise ValueError(f"Provided semester {s} was not found in the db.")
    if verbose:
        if len(semesters) > 1:
            print(
                "This script's updates for each semester are atomic, i.e. either all the "
                "updates for a certain semester are accepted by the database, or none of them are "
                "(if an error is encountered). If an error is encountered during the "
                "processing of a certain semester, any correctly completed updates for previously "
                "processed semesters will have already been accepted by the database."
            )
        else:
            print(
                "This script's updates for the given semester are atomic, i.e. either all the "
                "updates will be accepted by the database, or none of them will be "
                "(if an error is encountered)."
            )
    return semesters


def recompute_percent_open(semesters=None, verbose=False, semesters_precomputed=False):
    """
    Recompute the percent_open field for each section in the given semester(s).
    Args:
        semesters: The semesters argument should be a comma-separated list of string semesters
            corresponding to the semesters for which you want to recompute percent_open fields,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. It defaults to None,
            in which case only the current semester is used. If you supply the string "all",
            it will recompute for all semesters found in Courses in the db.
            If semesters_precomputed is set to True (non-default), then this argument should
            instead be a list of single string semesters.
        semesters_precomputed: If False (default), the semesters argument will expect a raw
            comma-separated string input. If True, the semesters argument will expect a list of
            individual string semesters.
        verbose: Set to True if you want this script to print its status as it goes,
            or keep as False (default) if you want the script to work silently.
    """

    current_semester = get_current_semester()
    semesters = (
        semesters if semesters_precomputed else get_semesters(semesters=semesters, verbose=verbose)
    )

    if verbose:
        print(f"Recomputing open percentages for semesters {str(semesters)}...")

    for semester_num, semester in enumerate(semesters):
        with transaction.atomic():
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.
            # If set_cache is True, we will set the current_demand_distribution_estimate variable
            # in cache

            if verbose:
                print(f"\nProcessing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.")

            StatusUpdate.objects.filter(section__course__semester=semester).select_for_update()

            sections = Section.objects.filter(course__semester=semester)
            num_erroneous_updates = 0
            num_total_updates = 0
            for section in sections:
                add_drop = get_add_drop_period(section.semester)
                add_drop_start = add_drop.estimated_start
                add_drop_end = add_drop.estimated_end

                status_updates = StatusUpdate.objects.filter(
                    section=section, created_at__gt=add_drop_start, created_at__lt=add_drop_end
                ).order_by("created_at")
                num_total_updates += len(status_updates)
                total_open_seconds = 0
                if not status_updates.exists():
                    try:
                        guess_status = (
                            StatusUpdate.objects.filter(
                                section=section, created_at__lte=add_drop_start
                            )
                            .latest("created_at")
                            .new_status
                        )
                    except StatusUpdate.DoesNotExist:
                        guess_status = "C"
                    section.percent_open = float(guess_status == "O")
                else:
                    last_dt = add_drop_start
                    last_status = status_updates.first().old_status
                    for update in status_updates:
                        if last_status != update.old_status:
                            num_erroneous_updates += 1
                        if last_status == "O" and update.new_status != "O":
                            total_open_seconds += (update.created_at - last_dt).total_seconds()
                        last_dt = update.created_at
                        last_status = update.new_status
                    section.percent_open = float(total_open_seconds) / float(
                        (status_updates.last().created_at - add_drop_start).total_seconds()
                    )
                    if section.semester != current_semester:
                        section.percent_open = float(
                            total_open_seconds
                            + int(last_status == "O") * (add_drop_end - last_dt).total_seconds()
                        ) / float((add_drop_end - add_drop_start).total_seconds())
                section.save()
            if verbose:
                print(
                    f"Finished calculating percent_open for {len(sections)} sections from "
                    f"semester {semester}, ignored {num_erroneous_updates} erroneous "
                    f"Status Updates (out of {num_total_updates} total Status Updates)"
                )
    if verbose:
        print(f"Finished recomputing open percentages for semesters {str(semesters)}.")


def recompute_registration_volumes(semesters=None, semesters_precomputed=False, verbose=False):
    """
    This script recomputes all PcaDemandDistributionEstimate objects for the given semester(s)
    based on saved Registration objects, as well as the registration_volume fields for all sections
    in the given semester(s).
    Args:
        semesters: The semesters argument should be a comma-separated list of string semesters
            corresponding to the semesters for which you want to recompute demand distribution
            estimate, i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. It
            defaults to None, in which case only the current semester is used. If you supply the
            string "all", it will recompute for all semesters found in Courses in the db.
            If semesters_precomputed is set to True (non-default), then this argument should
            instead be a list of single string semesters.
        semesters_precomputed: If False (default), the semesters argument will expect a raw
            comma-separated string input. If True, the semesters argument will expect a list of
            individual string semesters.
        verbose: Set to True if you want this script to print its status as it goes,
            or keep as False (default) if you want the script to work silently.
    """

    semesters = (
        semesters if semesters_precomputed else get_semesters(semesters=semesters, verbose=verbose)
    )

    if verbose:
        print(f"Computing most recent registration volumes for semesters {semesters} ...")
    with transaction.atomic():
        Section.objects.filter(course__semester__in=semesters).select_for_update().update(
            registration_volume=Coalesce(
                Subquery(
                    Registration.objects.filter(
                        section__id=OuterRef("id"), **Registration.is_active_filter()
                    )
                    .annotate(common=Value(1))
                    .values("common")
                    .annotate(count=Count("*"))
                    .values("count")[:1],
                ),
                Value(0),
            )
        )


# Filters defining which sections we will include in demand distribution estimates
demand_distribution_estimates_base_section_filters = (
    ~Q(
        course__department__code__in=WAITLIST_DEPARTMENT_CODES
    )  # Manually filter out classes from depts with waitlist systems during add/drop
    & Q(capacity__isnull=False, capacity__gt=0)
    & ~Q(course__semester__icontains="b")  # Filter out summer classes
    & Q(status_updates__section_id=F("id"))  # Filter out sections with no status updates
    & ~Q(
        id__in=Subquery(
            Restriction.objects.filter(description__icontains="permission").values_list(
                "sections__id", flat=True
            )
        )
    )  # Filter out sections that require permit for registration
    & ~Q(
        id__in=Subquery(
            Restriction.objects.filter(description__icontains="permission").values_list(
                "sections__id", flat=True
            )
        )
    )  # Filter out sections that require permit for registration
    & (
        Q(id__in=Subquery(Review.objects.all().values_list("section__id", flat=True)))
        | Q(course__semester=Subquery(Option.objects.filter(key="SEMESTER").values("value")[:1]))
    )  # Filter out sections from past semesters that do not have review data
)  # If you modify these filters, reflect the same changes in these corresponding filters:
# extra_metrics_filter in review/annotations/review_averages and
# plots_base_section_filters in review/views/course_reviews accordingly


def recompute_demand_distribution_estimates(
    semesters=None, semesters_precomputed=False, verbose=False
):
    """
    This script recomputes all PcaDemandDistributionEstimate objects for the given semester(s)
    based on saved Registration objects, as well as the registration_volume fields for all sections
    in the given semester(s).
    Args:
        semesters: The semesters argument should be a comma-separated list of string semesters
            corresponding to the semesters for which you want to recompute demand distribution
            estimate, i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. It
            defaults to None, in which case only the current semester is used. If you supply the
            string "all", it will recompute for all semesters found in Courses in the db.
            If semesters_precomputed is set to True (non-default), then this argument should
            instead be a list of single string semesters.
        semesters_precomputed: If False (default), the semesters argument will expect a raw
            comma-separated string input. If True, the semesters argument will expect a list of
            individual string semesters.
        verbose: Set to True if you want this script to print its status as it goes,
            or keep as False (default) if you want the script to work silently.
    """

    current_semester = get_current_semester()
    semesters = (
        semesters if semesters_precomputed else get_semesters(semesters=semesters, verbose=verbose)
    )

    # Recompute most recent registration volumes and open percentages
    recompute_registration_volumes(semesters=semesters, semesters_precomputed=True, verbose=verbose)
    recompute_percent_open(semesters=semesters, semesters_precomputed=True, verbose=verbose)

    print(f"Recomputing demand distribution estimates for semesters {str(semesters)}...")
    for semester_num, semester in enumerate(semesters):
        if "b" in semester.lower():
            if verbose:
                print(f"Skipping summer semester {semester}")
            continue
        set_cache = semester == current_semester

        cache_context = (
            cache.lock("current_demand_distribution_estimate")
            if (set_cache and hasattr(cache, "lock"))
            else nullcontext()
        )
        with transaction.atomic(), cache_context:
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.
            # If set_cache is True, we will set the current_demand_distribution_estimate variable
            # in cache

            add_drop_period = get_add_drop_period(semester)

            if verbose:
                print(f"Processing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.\n")
                print(
                    "Deleting existing PcaDemandDistributionEstimate objects for semester "
                    f"{semester} (so that we can recompute these objects)..."
                )
            PcaDemandDistributionEstimate.objects.filter(
                semester=semester
            ).select_for_update().delete()

            sections = dict()  # maps section id to section object (for this semester)
            volume_changes_map = dict()  # maps section id to list of volume changes
            status_updates_map = dict()  # maps section id to list of status updates

            iterator_wrapper = tqdm if verbose else (lambda x: x)
            if verbose:
                print("Indexing relevant sections...")
            for section in iterator_wrapper(
                Section.objects.filter(
                    demand_distribution_estimates_base_section_filters, course__semester=semester
                ).annotate(efficient_semester=F("course__semester"),)
            ):
                sections[section.id] = section
                volume_changes_map[section.id] = []
                status_updates_map[section.id] = []

            iterator_wrapper = tqdm if verbose else (lambda x: x)
            if verbose:
                print("Computing registration volume changes over time for each section...")
            for registration in iterator_wrapper(
                Registration.objects.filter(section_id__in=sections.keys())
                .annotate(section_capacity=F("section__capacity"))
                .select_for_update()
            ):
                section_id = registration.section_id
                volume_changes_map[section_id].append(
                    {"date": registration.created_at, "volume_change": 1}
                )
                deactivated_at = registration.deactivated_at
                if deactivated_at is not None:
                    volume_changes_map[section_id].append(
                        {"date": deactivated_at, "volume_change": -1}
                    )

            iterator_wrapper = tqdm if verbose else (lambda x: x)
            if verbose:
                print("Collecting status updates over time for each section...")
            for status_update in iterator_wrapper(
                StatusUpdate.objects.filter(
                    section_id__in=sections.keys(), in_add_drop_period=True
                ).select_for_update()
            ):
                section_id = status_update.section_id
                status_updates_map[section_id].append(
                    {
                        "date": status_update.created_at,
                        "old_status": status_update.old_status,
                        "new_status": status_update.new_status,
                    }
                )

            if verbose:
                print("Joining updates for each section and sorting...")
            all_changes = sorted(
                [
                    {"type": "volume_change", "section_id": section_id, **change}
                    for section_id, changes_list in volume_changes_map.items()
                    for change in changes_list
                ]
                + [
                    {"type": "status_update", "section_id": section_id, **update}
                    for section_id, status_updates_list in status_updates_map.items()
                    for update in status_updates_list
                ],
                key=lambda x: x["date"],
            )

            # Initialize variables to be maintained in our main all_changes loop
            latest_popularity_dist_estimate = None
            registration_volumes = {section_id: 0 for section_id in sections.keys()}
            demands = {section_id: 0 for section_id in sections.keys()}

            # Initialize section statuses
            section_status = {section_id: None for section_id in sections.keys()}
            for change in all_changes:
                section_id = change["section_id"]
                if change["type"] == "status_update":
                    if section_status[section_id] is None:
                        section_status[section_id] = change["old_status"]

            percent_through = (
                add_drop_period.get_percent_through_add_drop(timezone.now())
                if semester == current_semester
                else 1
            )
            if percent_through == 0:
                if verbose:
                    print(
                        f"Skipping semester {semester} because the add/drop period "
                        f"hasn't started yet."
                    )
                continue
            distribution_estimate_threshold = len(all_changes) // (
                ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES * percent_through
            )
            num_changes_without_estimate = 0

            iterator_wrapper = tqdm if verbose else (lambda x: x)
            if verbose:
                print(f"Creating PcaDemandDistributionEstimate objects for semester {semester}...")
            for change in iterator_wrapper(all_changes):
                section_id = change["section_id"]

                if section_status[section_id] is None:
                    section_status[section_id] = (
                        "O" if sections[section_id].percent_open > 0.5 else "C"
                    )
                if change["type"] == "status_update":
                    if section_status[section_id] != change["old_status"]:
                        # Ignore erroneous status updates
                        continue
                    section_status[section_id] = change["new_status"]
                    continue

                date = change["date"]
                volume_change = change["volume_change"]
                registration_volumes[section_id] += volume_change
                demands[section_id] = (
                    registration_volumes[section_id] / sections[section_id].capacity
                )

                max_id = max(demands.keys(), key=lambda x: demands[x])
                min_id = min(demands.keys(), key=lambda x: demands[x])
                if (
                    latest_popularity_dist_estimate is None
                    or section_id == latest_popularity_dist_estimate.highest_demand_section_id
                    or section_id == latest_popularity_dist_estimate.lowest_demand_section_id
                    or latest_popularity_dist_estimate.highest_demand_section_id != max_id
                    or latest_popularity_dist_estimate.lowest_demand_section_id != min_id
                    or num_changes_without_estimate >= distribution_estimate_threshold
                ):
                    num_changes_without_estimate = 0
                    closed_sections_demand_values = np.asarray(
                        [val for sec_id, val in demands.items() if section_status[sec_id] == "C"]
                    )
                    # "The term 'closed sections demand values' is sometimes abbreviated as 'csdv'
                    csdv_nonempty = len(closed_sections_demand_values) > 0
                    fit_alpha, fit_loc, fit_scale, mean_log_likelihood = (None, None, None, None)
                    if csdv_nonempty:
                        fit_alpha, fit_loc, fit_scale = stats.gamma.fit(
                            closed_sections_demand_values
                        )
                        mean_log_likelihood = stats.gamma.logpdf(
                            closed_sections_demand_values, fit_alpha, fit_loc, fit_scale
                        ).mean()

                    new_distribution_estimate = PcaDemandDistributionEstimate(
                        created_at=date,
                        semester=semester,
                        highest_demand_section=sections[max_id],
                        highest_demand_section_volume=registration_volumes[max_id],
                        lowest_demand_section=sections[min_id],
                        lowest_demand_section_volume=registration_volumes[min_id],
                        csdv_gamma_param_alpha=fit_alpha,
                        csdv_gamma_param_loc=fit_loc,
                        csdv_gamma_param_scale=fit_scale,
                        csdv_gamma_fit_mean_log_likelihood=mean_log_likelihood,
                        csdv_mean=(
                            np.mean(closed_sections_demand_values) if csdv_nonempty else None
                        ),
                        csdv_median=(
                            np.median(closed_sections_demand_values) if csdv_nonempty else None
                        ),
                        csdv_75th_percentile=(
                            np.percentile(closed_sections_demand_values, 75)
                            if csdv_nonempty
                            else None
                        ),
                    )
                    new_distribution_estimate.save(add_drop_period=add_drop_period)
                    new_distribution_estimate.created_at = date
                    new_distribution_estimate.save()
                    latest_popularity_dist_estimate = new_distribution_estimate
                else:
                    num_changes_without_estimate += 1

            if set_cache:
                if latest_popularity_dist_estimate is not None:
                    cache.set(
                        "current_demand_distribution_estimate",
                        latest_popularity_dist_estimate,
                        timeout=None,
                    )
                else:
                    cache.set("current_demand_distribution_estimate", None, timeout=None)

    print(
        "Finished recomputing demand distribution estimate and section registration_volume fields "
        f"for semesters {str(semesters)}."
    )


def recompute_stats(semesters=None, semesters_precomputed=False, verbose=False):
    """
    Recompute the percent_open field on each section, as well
    """
    load_add_drop_dates(verbose=True)
    if not semesters_precomputed:
        semesters = get_semesters(semesters=semesters, verbose=verbose)
    recompute_demand_distribution_estimates(
        semesters=semesters, semesters_precomputed=True, verbose=verbose
    )


class Command(BaseCommand):
    help = (
        "Recompute PCA demand distribution estimate, as well as the registration_volume "
        "and percent_open fields for all sections in the given semester(s)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters for which you want to recompute stats,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. If this argument
            is omitted, stats are only recomputed for the current semester.
            If you pass "all" to this argument, this script will recompute stats for
            all semesters found in Courses in the db.
                """
            ),
            nargs="?",
            default=None,
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        recompute_stats(semesters=kwargs["semesters"], verbose=True)
