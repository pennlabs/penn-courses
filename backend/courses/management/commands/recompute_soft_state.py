import logging
from textwrap import dedent

import numpy as np
import scipy.stats as stats
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Count, F, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from tqdm import tqdm

from alert.models import (
    PcaDemandDistributionEstimate,
    Registration,
    Section,
    validate_add_drop_semester,
)
from courses.management.commands.deduplicate_status_updates import deduplicate_status_updates
from courses.management.commands.load_add_drop_dates import (
    fill_in_add_drop_periods,
    load_add_drop_dates,
)
from courses.management.commands.recompute_topics import recompute_topics
from courses.models import Course, Meeting, StatusUpdate
from courses.util import (
    get_current_semester,
    get_or_create_add_drop_period,
    get_semesters,
    subquery_count_distinct,
)
from PennCourses.settings.base import ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES
from review.views import extra_metrics_section_filters


def recompute_num_activities():
    Course.objects.all().annotate(
        activity_count=subquery_count_distinct(
            Section.objects.filter(course_id=OuterRef("id")), column="activity"
        )
    ).update(num_activities=F("activity_count"))


def recompute_meeting_count():
    Section.objects.all().annotate(
        meeting_count=subquery_count_distinct(
            Meeting.objects.filter(section_id=OuterRef("id")), column="id"
        )
    ).update(num_meetings=F("meeting_count"))


def recompute_has_reviews():
    with connection.cursor() as cursor:
        cursor.execute(
            """
        UPDATE "courses_section" AS U0
        SET "has_reviews" = CASE WHEN
            EXISTS (SELECT id FROM "review_review" AS U1
                WHERE U0."id" = U1."section_id"
                    AND U1."responses" > 0)
            THEN true ELSE false
        END
        """
        )


def recompute_has_status_updates():
    with connection.cursor() as cursor:
        cursor.execute(
            """
        UPDATE "courses_section" AS U0
        SET "has_status_updates" = CASE WHEN
            EXISTS (SELECT id FROM "courses_statusupdate" AS U1
                WHERE U0."id" = U1."section_id")
            THEN true ELSE false
        END
        """
        )


def recompute_enrollment():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE courses_section s1
            SET enrollment = (
                SELECT SUM(s2.code_specific_enrollment)
                FROM courses_section AS s2
                INNER JOIN courses_course AS c2 ON s2.course_id = c2.id
                WHERE s1.code = s2.code AND c2.primary_listing_id = (
                    SELECT primary_listing_id
                    FROM courses_course
                    WHERE id = s1.course_id
                )
            )
            """
        )


# course credits = sum(section credis for all activities for sections below 500)
# the < 500 heuristic comes from here:
# https://provider.www.upenn.edu/computing/da/dw/student/enrollment_section_type.e.html
COURSE_CREDITS_RAW_SQL = dedent(
    """
    WITH CourseCredits AS (
        SELECT U0."id", SUM(U2."activity_cus") AS total_credits
        FROM "courses_course" U0
        INNER JOIN (
            SELECT MAX(U1."credits") AS "activity_cus", U1."course_id"
            FROM "courses_section" U1
            WHERE U1."code" < '500' AND (U1."status" <> 'X' OR U1."status" <> '')
            GROUP BY U1."course_id", U1."activity"
        ) AS U2
        ON U0."id" = U2."course_id"
        GROUP BY U0."id"
    )

    UPDATE "courses_course" U0
    SET "credits" = CourseCredits.total_credits
    FROM CourseCredits
    WHERE U0."id" = CourseCredits."id";
"""
)


def recompute_course_credits(
    model=Course,  # so this function can be used in migrations (see django.db.migrations.RunPython)
):
    with connection.cursor() as cursor:
        cursor.execute(COURSE_CREDITS_RAW_SQL)


def recompute_precomputed_fields(verbose=False):
    """
    Recomputes the following precomputed fields:
        - Course.num_activities
        - Course.credits
        - Section.num_meetings
        - Section.has_reviews
        - Section.has_status_updates

    :param verbose: Whether to print status/progress updates.
    """
    if verbose:
        print("Recomputing precomputed fields...")

    if verbose:
        print("\tRecomputing Course.num_activities")
    recompute_num_activities()
    if verbose:
        print("\tRecomputing Course.credits")
    recompute_course_credits()
    if verbose:
        print("\tRecomputing Section.num_meetings")
    recompute_meeting_count()
    if verbose:
        print("\tRecomputing Section.has_reviews")
    recompute_has_reviews()
    if verbose:
        print("\tRecomputing Section.has_status_updates")
    recompute_has_status_updates()
    if verbose:
        print("\tRecomputing Section.enrollment")
    recompute_enrollment()

    if verbose:
        print("Done recomputing precomputed fields.")


def recompute_percent_open(semesters: list[str], verbose=False):
    """
    Recomputes the percent_open field for each section in the given semester(s).

    :param semesters: Semesters for which you want to recompute percent_open fields.
    :param verbose: Whether to print status/progress updates.
    """

    current_semester = get_current_semester()

    if verbose:
        print(f"Recomputing open percentages for semesters {semesters}...")

    for semester_num, semester in enumerate(semesters):
        with transaction.atomic():
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.

            if verbose:
                print(f"\nProcessing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.")

            add_drop = get_or_create_add_drop_period(semester)
            add_drop_start = add_drop.estimated_start
            add_drop_end = add_drop.estimated_end

            StatusUpdate.objects.filter(section__course__semester=semester).select_for_update()

            sections = Section.objects.filter(course__semester=semester)
            num_erroneous_updates = 0
            num_total_updates = 0
            for section in sections:
                status_updates = StatusUpdate.objects.filter(
                    section=section,
                    created_at__gt=add_drop_start,
                    created_at__lt=add_drop_end,
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
                        guess_status = section.status
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
                    f"semester {semester}, encountered {num_erroneous_updates} erroneous "
                    f"Status Updates (out of {num_total_updates} total Status Updates)"
                )
    if verbose:
        print(f"Finished recomputing open percentages for semesters {semesters}.")


def recompute_registration_volumes(semesters: list[str], verbose=False):
    """
    Recomputes the registration_volume fields for all sections in the given semester(s).

    :param semesters: Semesters for which you want to recompute registration volumes.
    :param verbose: Whether to print status/progress updates.
    """

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


def recompute_demand_distribution_estimates(semesters: list[str], verbose=False):
    """
    This script recomputes all PcaDemandDistributionEstimate objects for the given semester(s)
    based on saved Registration objects. In doing so, it also recomputes the registration_volume
    and percent_open fields for all sections in the given semester(s)
    (by calling recompute_registration_volumes and recompute_percent_open).

    :param semesters: Semesters for which you want to recompute demand distribution estimates.
    :param verbose: Whether to print status/progress updates.
    """

    current_semester = get_current_semester()

    recompute_precomputed_fields(verbose=verbose)
    recompute_registration_volumes(semesters=semesters, verbose=verbose)
    recompute_percent_open(semesters=semesters, verbose=verbose)

    if verbose:
        print(f"Recomputing demand distribution estimates for semesters {semesters}...")
    for semester_num, semester in enumerate(semesters):
        try:
            validate_add_drop_semester(semester)
        except ValidationError:
            if verbose:
                print(f"Skipping semester {semester} (unsupported kind for stats).")
            continue
        add_drop_period = get_or_create_add_drop_period(semester)
        set_cache = semester == current_semester

        with transaction.atomic():
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.
            # If set_cache is True, we will set the current_demand_distribution_estimate variable
            # in cache

            if verbose:
                print(f"Processing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.\n")
                print(
                    "Deleting existing PcaDemandDistributionEstimate objects for semester "
                    f"{semester} (so that we can recompute these objects)..."
                )
            PcaDemandDistributionEstimate.objects.filter(
                semester=semester
            ).select_for_update().delete()

            section_id_to_object = dict()  # maps section id to section object (for this semester)
            volume_changes_map = dict()  # maps section id to list of volume changes
            status_updates_map = dict()  # maps section id to list of status updates

            if verbose:
                print("Indexing relevant sections...")
            for section in tqdm(
                Section.objects.filter(extra_metrics_section_filters, course__semester=semester)
                .annotate(
                    efficient_semester=F("course__semester"),
                )
                .distinct(),
                disable=not verbose,
            ):
                section_id_to_object[section.id] = section
                volume_changes_map[section.id] = []
                status_updates_map[section.id] = []

            if verbose:
                print("Computing registration volume changes over time for each section...")
            for registration in tqdm(
                Registration.objects.filter(section_id__in=section_id_to_object.keys())
                .annotate(section_capacity=F("section__capacity"))
                .select_for_update(),
                disable=not verbose,
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

            if verbose:
                print("Collecting status updates over time for each section...")
            for status_update in tqdm(
                StatusUpdate.objects.filter(
                    section_id__in=section_id_to_object.keys(), in_add_drop_period=True
                ).select_for_update(),
                disable=not verbose,
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
                    {"type": "status_update", "section_id": section_id, **update}
                    for section_id, status_updates_list in status_updates_map.items()
                    for update in status_updates_list
                ]
                + [
                    {"type": "volume_change", "section_id": section_id, **change}
                    for section_id, changes_list in volume_changes_map.items()
                    for change in changes_list
                ],
                key=lambda x: (x["date"], int(x["type"] != "status_update")),
                # put status updates first on matching dates
            )

            # Initialize variables to be maintained in our main all_changes loop
            latest_popularity_dist_estimate = None
            registration_volumes = {section_id: 0 for section_id in section_id_to_object.keys()}
            demands = {section_id: 0 for section_id in section_id_to_object.keys()}

            # Initialize section statuses
            section_status = {section_id: None for section_id in section_id_to_object.keys()}
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
            distribution_estimate_threshold = sum(
                len(changes_list) for changes_list in volume_changes_map.values()
            ) // (ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES * percent_through)
            num_changes_without_estimate = 0

            if verbose:
                print(f"Creating PcaDemandDistributionEstimate objects for semester {semester}...")
            for change in tqdm(all_changes, disable=not verbose):
                section_id = change["section_id"]

                if section_status[section_id] is None:
                    section_status[section_id] = (
                        "O" if section_id_to_object[section_id].percent_open > 0.5 else "C"
                    )
                if change["type"] == "status_update":
                    section_status[section_id] = change["new_status"]
                    continue

                date = change["date"]
                volume_change = change["volume_change"]
                registration_volumes[section_id] += volume_change
                demands[section_id] = (
                    registration_volumes[section_id] / section_id_to_object[section_id].capacity
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
                    csrdv_frac_zero, fit_shape, fit_loc, fit_scale = (
                        None,
                        None,
                        None,
                        None,
                    )
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

                    latest_popularity_dist_estimate = PcaDemandDistributionEstimate(
                        created_at=date,
                        semester=semester,
                        highest_demand_section=section_id_to_object[max_id],
                        highest_demand_section_volume=registration_volumes[max_id],
                        lowest_demand_section=section_id_to_object[min_id],
                        lowest_demand_section_volume=registration_volumes[min_id],
                        csrdv_frac_zero=csrdv_frac_zero,
                        csprdv_lognorm_param_shape=fit_shape,
                        csprdv_lognorm_param_loc=fit_loc,
                        csprdv_lognorm_param_scale=fit_scale,
                    )
                    latest_popularity_dist_estimate.save(add_drop_period=add_drop_period)
                    latest_popularity_dist_estimate.created_at = date
                    latest_popularity_dist_estimate.save(add_drop_period=add_drop_period)
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

    if verbose:
        print(
            "Finished recomputing demand distribution estimate and section registration_volume "
            f"fields for semesters {semesters}."
        )


def recompute_soft_state(semesters: list[str], verbose=False):
    recompute_topics(min_semester=min(semesters), verbose=verbose)
    adp_semesters = fill_in_add_drop_periods(verbose=verbose).intersection(semesters)
    load_add_drop_dates(verbose=verbose)
    deduplicate_status_updates(semesters=adp_semesters, verbose=verbose)
    recompute_demand_distribution_estimates(semesters=adp_semesters, verbose=verbose)


class Command(BaseCommand):
    help = (
        "Recomputes PCA demand distribution estimates, as well as the registration_volume "
        "and percent_open fields for all sections in the given semester(s). "
        "Fills in add drop periods, loads add drop dates, and deduplicates status updates. "
        "Recomputes topics from the parent_course graph. "
        "More generally, this script is the place for recomputing any 'soft state' (state that is "
        "not the source of truth / is derived from other data in our DB)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters for which you want to recompute soft state,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. If this argument
            is omitted, soft state is only recomputed for the current semester.
            If you pass "all" to this argument, this script will recompute soft state for
            all semesters found in Courses in the db.
                """
            ),
            default=None,
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        print(
            "Each step executed in this command is atomic per-semester "
            "(e.g., topics are recomputed for each semester atomically). "
            "If an error is encountered, all changes from that step for that semester "
            "will be rolled back. "
            "Any changes made to previous semesters or previous steps will persist."
        )

        semesters = get_semesters(kwargs["semesters"])
        recompute_soft_state(semesters=semesters, verbose=True)
