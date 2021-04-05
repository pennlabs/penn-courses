import logging
import operator
from contextlib import nullcontext
from decimal import Decimal
from textwrap import dedent

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from tqdm import tqdm

from alert.models import AddDropPeriod, PcaDemandExtrema, Registration, Section
from courses.management.commands.load_add_drop_dates import load_add_drop_dates
from courses.models import Course, StatusUpdate
from courses.util import get_current_semester


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


def recompute_demand_extrema(semesters=None, semesters_precomputed=False, verbose=False):
    """
    This script recomputes all PcaDemandExtrema objects for the given semester(s)
    based on saved Registration objects, as well as the registration_volume fields for all sections
    in the given semester(s).
    Args:
        semesters: The semesters argument should be a comma-separated list of string semesters
            corresponding to the semesters for which you want to recompute demand extrema,
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

    print(
        "Recomputing demand extrema and section registration_volume fields "
        f"for semesters {str(semesters)}..."
    )

    for semester_num, semester in enumerate(semesters):
        set_cache = semester == current_semester
        cache_context = (
            cache.lock("current_demand_extrema")
            if (set_cache and hasattr(cache, "lock"))
            else nullcontext()
        )
        with transaction.atomic(), cache_context:
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.
            # If set_cache is True, we will set the current_demand_extrema variable in cache

            add_drop_period = AddDropPeriod.get(semester=semester)

            if verbose:
                print(f"Processing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.\n")
                print(
                    "Deleting existing PcaDemandExtrema objects for semester "
                    f"{semester} (so that we can recompute these objects)..."
                )
            PcaDemandExtrema.objects.filter(semester=semester).select_for_update().delete()

            if verbose:
                print("Computing registration volumes for each section...")
            Section.objects.filter(course__semester=semester).select_for_update().update(
                registration_volume=Coalesce(
                    Subquery(
                        Registration.objects.filter(
                            section__pk=OuterRef("pk"), **Registration.is_active_filter()
                        )
                        .values("pk")
                        .annotate(count=Count("pk"))
                        .values("count")
                    ),
                    Value(0),
                )
            )

            iterator = (
                Registration.objects.filter(section__course__semester=semester)
                .select_related("section")
                .select_for_update()
                .order_by("created_at")
            )
            if verbose:
                print("Computing registration volume changes over time for each section...")
                iterator = tqdm(iterator, total=iterator.count())

            volume_changes_map = dict()
            capacities = dict()
            sections = dict()
            for registration in iterator:
                full_code = registration.section.full_code
                sections[full_code] = registration.section
                if registration.section.capacity is None or registration.section.capacity <= 0:
                    # Ignore sections with invalid capacities
                    continue
                if full_code not in capacities:
                    capacities[full_code] = registration.section.capacity
                if full_code not in volume_changes_map:
                    volume_changes_map[full_code] = []
                volume_changes_map[full_code].append(
                    {"date": registration.created_at, "volume_change": 1}
                )
                deactivated_at = registration.deactivated_at
                if deactivated_at is not None:
                    volume_changes_map[full_code].append(
                        {"date": deactivated_at, "volume_change": -1}
                    )

            iterator = volume_changes_map.items()
            if verbose:
                print("Joining updates for each section and sorting...")
                iterator = tqdm(iterator, total=len(iterator))
            all_changes = sorted(
                [
                    {"full_code": full_code, **data}
                    for full_code, changes_list in iterator
                    for data in changes_list
                ],
                key=lambda x: x["date"],
            )

            iterator = all_changes
            if verbose:
                print(f"Creating PcaDemandExtrema objects for semester {semester}...")
                iterator = tqdm(iterator, total=len(iterator))

            latest_pcape = None
            registration_volumes = dict()
            demands = dict()

            for change in all_changes:
                full_code = change["full_code"]
                date = change["date"]
                volume_change = change["volume_change"]
                if latest_pcape is None and volume_change > 0:
                    registration_volumes[full_code] = volume_change
                    new_extrema = PcaDemandExtrema(
                        created_at=date,
                        semester=semester,
                        most_popular_section=sections[full_code],
                        most_popular_volume=volume_change,
                        least_popular_section=sections[full_code],
                        least_popular_volume=volume_change,
                    )
                    new_extrema.save(add_drop_period=add_drop_period)
                    latest_pcape = new_extrema
                else:
                    if full_code not in registration_volumes:
                        registration_volumes[full_code] = 0
                    registration_volumes[full_code] += volume_change
                    demands[full_code] = registration_volumes[full_code] / capacities[full_code]
                    new_most_popular = None
                    if full_code != latest_pcape.most_popular_section.full_code:
                        if demands[full_code] > latest_pcape.highest_raw_demand:
                            new_most_popular = full_code
                    else:
                        if volume_change < 0:
                            max_code, max_val = max(demands.items(), key=operator.itemgetter(1))
                            if max_val > latest_pcape.highest_raw_demand:
                                new_most_popular = max_code
                    if new_most_popular is not None:
                        new_extrema = PcaDemandExtrema(
                            created_at=date,
                            semester=semester,
                            most_popular_section=registration_volumes[new_most_popular],
                            most_popular_volume=sections[new_most_popular],
                            least_popular_section=latest_pcape.least_popular_section,
                            least_popular_volume=latest_pcape.least_popular_volume,
                        )
                        new_extrema.save(add_drop_period=add_drop_period)
                        latest_pcape = new_extrema
                    new_least_popular = None
                    if full_code != latest_pcape.least_popular_section.full_code:
                        if demands[full_code] < latest_pcape.lowest_raw_demand:
                            new_least_popular = full_code
                    else:
                        if volume_change < 0:
                            max_code, max_val = max(demands.items(), key=operator.itemgetter(1))
                            if max_val > latest_pcape.highest_raw_demand:
                                new_least_popular = max_code
                    if new_least_popular is not None:
                        new_extrema = PcaDemandExtrema(
                            created_at=date,
                            semester=semester,
                            most_popular_section=latest_pcape.most_popular_section,
                            most_popular_volume=latest_pcape.most_popular_volume,
                            least_popular_section=registration_volumes[new_least_popular],
                            least_popular_volume=sections[new_least_popular],
                        )
                        new_extrema.save(add_drop_period=add_drop_period)
                        latest_pcape = new_extrema

            if set_cache:
                if latest_pcape is not None:
                    cache.set("current_demand_extrema", latest_pcape, timeout=None)
                else:
                    cache.set("current_demand_extrema", None, timeout=None)

    print(
        "Finished recomputing demand extrema and section registration_volume fields "
        f"for semesters {str(semesters)}."
    )


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
            # If set_cache is True, we will set the current_demand_extrema variable in cache

            if verbose:
                print(f"Processing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.\n")

            StatusUpdate.objects.filter(section__course__semester=semester).select_for_update()

            sections = Section.objects.filter(section__course__semester=semester)
            num_erroneous_updates = 0
            num_total_updates = 0
            for section in sections:
                add_drop = AddDropPeriod.objects.get(semester=section.semester)
                add_drop_start = add_drop.estimated_start
                add_drop_end = add_drop.estimated_end

                status_updates = StatusUpdate.objects.filter(
                    section=section, created_at__gt=add_drop_start, created_at__lt=add_drop_end
                ).order_by("created_at")
                num_total_updates += len(status_updates)
                total_open_seconds = 0
                if not status_updates.exists():
                    section.percent_open = 0
                else:
                    last_dt = add_drop_start
                    try:
                        last_status = (
                            StatusUpdate.objects.filter(
                                section=section, created_at__lte=add_drop_start
                            )
                            .latest("created_at")
                            .new_status
                        )
                    except StatusUpdate.DoesNotExist:
                        last_status = "O"
                    for update in status_updates:
                        if last_status != update.old_status:
                            num_erroneous_updates += 1
                        if last_status == "O" and update.new_status != "O":
                            total_open_seconds += (update.created_at - last_dt).total_seconds()
                        last_dt = update.created_at
                        last_status = update.new_status
                    section.percent_open = Decimal(total_open_seconds) / Decimal(
                        (status_updates[-1].created_at - add_drop_start).total_seconds()
                    )
                if section.semester != current_semester:
                    section.percent_open = Decimal(
                        total_open_seconds
                        + int(last_status == "O") * (add_drop_end - last_dt).total_seconds()
                    ) / Decimal((add_drop_end - add_drop_start).total_seconds())
                section.save()
            if verbose:
                print(
                    f"Finished calculating percent_open for {len(sections)} sections from "
                    f"semester {semester}, ignored {num_erroneous_updates} erroneous "
                    f"Status Updates (out of {num_total_updates} total Status Updates)"
                )
    if verbose:
        print(f"Finished recomputing open percentages for semesters {str(semesters)}.")


def recompute_stats(semesters=None, verbose=False):
    """
    Recompute the percent_open field on each section, as well
    """
    load_add_drop_dates(verbose=True)
    semesters = get_semesters(semesters=semesters, verbose=verbose)
    recompute_demand_extrema(semesters=semesters, semesters_precomputed=True, verbose=verbose)
    recompute_percent_open(semesters=semesters, semesters_precomputed=True, verbose=verbose)


class Command(BaseCommand):
    help = (
        "Recompute PCA demand extrema, as well as the registration_volume "
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
