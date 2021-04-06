import logging
from contextlib import nullcontext
from textwrap import dedent

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, F, OuterRef, Subquery, Value
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

            add_drop_period = AddDropPeriod.objects.get(semester=semester)

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
                            section__id=OuterRef("id"), **Registration.is_active_filter()
                        )
                        .values("id")
                        .annotate(count=Count("id"))
                        .values("count")
                    ),
                    Value(0),
                )
            )

            registrations = (
                Registration.objects.filter(section__course__semester=semester)
                .select_related("section")
                .select_for_update()
                .order_by("created_at")
            )
            if verbose:
                print("Computing registration volume changes over time for each section...")
                registrations = tqdm(registrations, total=registrations.count())

            volume_changes_map = dict()  # maps full_code to list of volume changes
            sections = dict()  # maps full_code to section object (for this semester)
            for section in Section.objects.filter(
                course__semester=semester, capacity__isnull=False, capacity__gt=0
            ).annotate(efficient_semester=F("course__semester")):
                sections[section.full_code] = section
                volume_changes_map[section.full_code] = []
            for registration in registrations:
                if registration.section.capacity is None or registration.section.capacity <= 0:
                    # Ignore sections with invalid capacities
                    continue
                full_code = registration.section.full_code
                volume_changes_map[full_code].append(
                    {"date": registration.created_at, "volume_change": 1}
                )
                deactivated_at = registration.deactivated_at
                if deactivated_at is not None:
                    volume_changes_map[full_code].append(
                        {"date": deactivated_at, "volume_change": -1}
                    )

            if verbose:
                print("Joining updates for each section and sorting...")
            all_changes = sorted(
                [
                    {"full_code": full_code, **data}
                    for full_code, changes_list in volume_changes_map.items()
                    for data in changes_list
                ],
                key=lambda x: x["date"],
            )

            if verbose:
                print(f"Creating PcaDemandExtrema objects for semester {semester}...")
                all_changes = tqdm(all_changes, total=len(all_changes))

            latest_pcade = None
            registration_volumes = {full_code: 0 for full_code in sections.keys()}
            demands = {full_code: 0 for full_code in sections.keys()}

            for change in all_changes:
                full_code = change["full_code"]
                date = change["date"]
                volume_change = change["volume_change"]
                registration_volumes[full_code] += volume_change
                demands[full_code] = registration_volumes[full_code] / sections[full_code].capacity
                if latest_pcade is None:
                    new_extrema = PcaDemandExtrema(
                        created_at=date,
                        semester=semester,
                        most_popular_section=sections[full_code],
                        most_popular_volume=volume_change,
                        least_popular_section=sections[full_code],
                        least_popular_volume=volume_change,
                    )
                    new_extrema.save(add_drop_period=add_drop_period)
                    new_extrema.created_at = date
                    new_extrema.save()
                    latest_pcade = new_extrema
                else:
                    max_code = max(demands.keys(), key=lambda x: demands[x])
                    min_code = min(demands.keys(), key=lambda x: demands[x])
                    if (
                        full_code == latest_pcade.most_popular_section.full_code
                        or full_code == latest_pcade.least_popular_section.full_code
                        or latest_pcade.most_popular_section.full_code != max_code
                        or latest_pcade.least_popular_section.full_code != min_code
                    ):
                        new_extrema = PcaDemandExtrema(
                            created_at=date,
                            semester=semester,
                            most_popular_section=sections[max_code],
                            most_popular_volume=registration_volumes[max_code],
                            least_popular_section=sections[min_code],
                            least_popular_volume=registration_volumes[min_code],
                        )
                        new_extrema.save(add_drop_period=add_drop_period)
                        new_extrema.created_at = date
                        new_extrema.save()
                        latest_pcade = new_extrema

            if set_cache:
                if latest_pcade is not None:
                    cache.set("current_demand_extrema", latest_pcade, timeout=None)
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
                print(f"\nProcessing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.")

            StatusUpdate.objects.filter(section__course__semester=semester).select_for_update()

            sections = Section.objects.filter(course__semester=semester)
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
