import logging
import operator
from contextlib import nullcontext

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from tqdm import tqdm

from alert.models import PcaDemandExtrema, Registration, Section
from courses.models import Course
from courses.util import get_current_semester


def recompute_demand_extrema(semesters=None, verbose=False):
    """
    Args:
        semesters: The semester argument should be a comma-separated list of string semesters
            corresponding to the semesters for which you want to recompute demand extrema,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020. It defaults to None,
            in which case only the current semester is used. If you supply the string "all",
            it will recompute demand extrema for all semesters found in Courses in the db.
        verbose: Set to True if you want this script to print its status as it goes,
            or keep as False (default) if you want the script to work silently.
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

    for semester_num, semester in enumerate(semesters):
        set_cache = semester == current_semester
        cache_context = (
            cache.lock("current_demand_extrema")
            if (set_cache and hasattr(cache, "lock"))
            else nullcontext()
        )
        with transaction.atomic(), cache_context:
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for semester_to_compute succeeds.
            # If set_cache is True, we will set the current_demand_extrema variable in cache

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

            iterator = (
                Registration.objects.filter(section__course__semester=semester)
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
                deactivate_candidate_dates = [
                    registration.notification_sent_at,
                    registration.cancelled_at,
                    registration.deleted_at,
                ]  # check Registration.is_active_filter to ensure
                # that this definition of "active" is up-to-date
                deactivated_at = min(
                    [d for d in deactivate_candidate_dates if d is not None], default=None
                )
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
            popularities = dict()

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
                    new_extrema.save()
                    latest_pcape = new_extrema
                else:
                    if full_code not in registration_volumes:
                        registration_volumes[full_code] = 0
                    registration_volumes[full_code] += volume_change
                    popularities[full_code] = (
                        registration_volumes[full_code] / capacities[full_code]
                    )
                    new_most_popular = None
                    if full_code != latest_pcape.most_popular_section.full_code:
                        if popularities[full_code] > latest_pcape.highest_raw_demand:
                            new_most_popular = full_code
                    else:
                        if volume_change < 0:
                            max_code, max_val = max(
                                popularities.items(), key=operator.itemgetter(1)
                            )
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
                        new_extrema.save()
                        latest_pcape = new_extrema
                    new_least_popular = None
                    if full_code != latest_pcape.least_popular_section.full_code:
                        if popularities[full_code] < latest_pcape.lowest_raw_demand:
                            new_least_popular = full_code
                    else:
                        if volume_change < 0:
                            max_code, max_val = max(
                                popularities.items(), key=operator.itemgetter(1)
                            )
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
                        new_extrema.save()
                        latest_pcape = new_extrema

            if set_cache:
                if latest_pcape is not None:
                    cache.set("current_demand_extrema", latest_pcape, timeout=None)
                else:
                    cache.set("current_demand_extrema", None, timeout=None)

            if verbose:
                print("Done.")


class Command(BaseCommand):
    help = "Compute PCA demand extrema for a semester."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semester",
            type=str,
            help="The semester for which to compute PCA demand extrema.",
            nargs="?",
            default=None,
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        print(f"Recomputing PCA demand extrema for semester {kwargs['semester']}")
        recompute_demand_extrema(semesters=kwargs["semester"], verbose=True)
