import logging
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Set

from django.core.management import BaseCommand
from tqdm import tqdm

from courses.models import Instructor
from review.management.commands.clearcache import clear_cache


# Statistic keys
INSTRUCTORS_KEPT = "instructors kept"
INSTRUCTORS_REMOVED = "instructors removed"
SECTIONS_MODIFIED = "sections modified"
REVIEWS_MODIFIED = "reviews modified"
INSTRUCTORS_UNMERGED = "instructors unmerged"


def batch_duplicates(qs, get_prop=None, union_find=None) -> List[Set[Instructor]]:
    """
    Group queryset rows by a property defined in `get_prop()` (or alternatively
    specify groups with a union find dictionary). Return a list of groups of size > 1.
    :param qs: Queryset of instructors to use
    :param get_prop: Function mapping a row to a value to group on.
        If `get_prop` returns `None`, don't include the row in the groupings.
    :param union_find: Alternatively to specifying `get_prop`, you can specify
        groups with a union find dictionary (mapping instructor id to
        a root instructor id representing the group).
        This kwarg accepts a function mapping `qs` to a union find dictionary.
    :return: List of instructor groups of size > 1.
    """
    rows_by_prop = defaultdict(set)
    if union_find:
        union_find = union_find(qs)
        for row in qs:
            rows_by_prop[union_find[row.id]].add(row)
    else:
        assert get_prop
        for row in qs:
            rows_by_prop[get_prop(row)].add(row)
    return [rows for prop, rows in rows_by_prop.items() if prop and len(rows) > 1]


def resolve_duplicates(
    duplicate_instructor_groups: List[Set[Instructor]],
    dry_run: bool,
    stat=None,
    force=False,
):
    """
    Given a list of list of duplicate instructor groups, resolve the foreign key and many-to-many
    relationships among duplicates to all point to the same instance.

    :param duplicate_instructor_groups: List of sets of duplicate instructors
    e.g. [{a1, a2, a3}, {b1, b2}]
    :param dry_run: If true, just calculate stats without actually modifying the database.
    :param stat: Function to collect statistics.
    :param force: Manually override conflicting user information.
    """
    if not stat:
        stat = lambda key, amt=1, element=None: None  # noqa E731
    for instructor_set in tqdm(duplicate_instructor_groups):
        # Find a primary instance in the duplicate set. This should be the instance that is most
        # "complete" -- in the case of instructors, this means that there is a linked user object.
        potential_primary = [inst for inst in instructor_set if inst.user is not None]
        # If no instance has a linked user, just pick one instructor.
        if len(potential_primary) == 0:
            stat(INSTRUCTORS_KEPT, 1)
            primary_instructor = max(instructor_set, key=lambda i: i.updated_at)
        # If there's only one user with a linked user object, select that as the primary.
        # This should be the case that is hit most often.
        elif len(potential_primary) == 1:
            stat(INSTRUCTORS_KEPT, 1)
            primary_instructor = potential_primary[0]
        else:
            # If all potential primary rows relate to the same user (with the same pk),
            # go ahead and choose one arbitrarily.
            if len(set([inst.user.pk for inst in potential_primary])) == 1 or force:
                stat(INSTRUCTORS_KEPT, 1)
                primary_instructor = max(potential_primary, key=lambda i: i.updated_at)
            # Otherwise, we don't have enough information to merge automatically. There are multiple
            # instructors marked as duplicates, but they link to different users and so could be
            # different people. Report the PKs of these instructors in the statistics, but don't
            # merge.
            else:
                stat(INSTRUCTORS_KEPT, len(instructor_set))
                stat(INSTRUCTORS_UNMERGED, element=[i.pk for i in instructor_set])
                # We don't have enough information to do this merge.
                continue

        # Filter for all instructors that aren't the primary.
        duplicate_instructors = instructor_set - {primary_instructor}
        # Transfer the sections and reviews of all non-primary instances to the primary instance.
        for duplicate_instructor in duplicate_instructors:
            for section in duplicate_instructor.section_set.all():
                stat(SECTIONS_MODIFIED, 1)
                if not dry_run:
                    section.instructors.remove(duplicate_instructor)
                    section.instructors.add(primary_instructor)

            for review in duplicate_instructor.review_set.all():
                stat(REVIEWS_MODIFIED, 1)
                if not dry_run:
                    review.instructor = primary_instructor
                    review.save()

            stat(INSTRUCTORS_REMOVED, 1)
            if not dry_run:
                duplicate_instructor.delete()


"""
Strategy definitions. Keys are the strategy name, values are lambdas
which resolve a list of duplicate lists when called. The lambdas are to ensure
lazy evaluation, since we won't necessarily be running all (or any) of the
given strategies.
"""


def first_last_name_sections_uf(instructors):
    """
    Groups instructors if they share a first name / last name, and have
    taught the same section.
    """

    def get_first_last(name):
        components = name.split(" ")
        return (components[0], components[-1])

    union_find = {inst.id: inst.id for inst in instructors}

    for inst in tqdm(instructors):
        inst_first_last = get_first_last(inst.name)
        for section in inst.section_set.all():
            for other_inst in section.instructors.all():
                if inst_first_last == get_first_last(other_inst.name):
                    union_find[inst.id] = union_find[other_inst.id]

    def get_root_id(inst_id):
        while union_find[inst_id] != inst_id:
            inst_id = union_find[inst_id]
        return inst_id

    for inst_id in union_find:
        union_find[inst_id] = get_root_id(inst_id)

    return union_find


strategies: Dict[str, Callable[[], List[Set[Instructor]]]] = {
    "case-insensitive": lambda: batch_duplicates(
        Instructor.objects.all().prefetch_related("section_set", "review_set"),
        lambda row: row.name.lower(),
    ),
    "pennid": lambda: batch_duplicates(
        Instructor.objects.all().prefetch_related("section_set", "review_set"),
        lambda row: row.user_id,
    ),
    "first-last-name-sections": lambda: batch_duplicates(
        Instructor.objects.all().prefetch_related(
            "section_set", "review_set", "section_set__instructors"
        ),
        union_find=lambda rows: first_last_name_sections_uf(rows),
    ),
}


class Command(BaseCommand):
    help = """
    Merge duplicate instructor entries through different strategies.

    case-insensitive: Merge instructors with the same name but different cases [O'leary, O'Leary]
    pennid: Merge instructors with the same pennid
    first-last-name-sections: Merge instructors based on firstname, lastname and shared sections.
    """

    def add_arguments(self, parser):
        parser.add_argument("--dryrun", action="store_true", help="perform a dry run of merge.")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--instructor",
            "-i",
            action="append",
            dest="manual",
            help="manually merge instructors with the provided IDs.",
            default=list(),
        )
        group.add_argument("--strategy", "-s", dest="strategies", action="append")
        group.add_argument("--all", "-a", action="store_const", const=None, dest="strategies")

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        dry_run = kwargs["dryrun"]
        manual_merge: List[str] = kwargs["manual"]
        selected_strategies: Optional[List[str]] = kwargs["strategies"]

        stats = dict()

        def stat(key, amt=1, element=None):
            """
            Helper function to keep track of how many rows we are changing
            """
            value = stats.get(key, 0)
            if element is None:
                stats[key] = value + amt
            else:
                stats.setdefault(key, []).append(element)

        def run_merge(strat: Callable[[], List[Set[Instructor]]], force=False):
            """
            Run a merge pass, printing out helpful messages along the way.
            """
            print("Finding duplicates...")
            duplicates = strat()
            print(f"Found {len(duplicates)} instructors with multiple rows. Merging records...")
            resolve_duplicates(duplicates, dry_run, stat, force)

        if len(manual_merge) > 0:
            print("***Merging records manually***")
            run_merge(
                lambda: [set(Instructor.objects.filter(pk__in=manual_merge))],
                force=True,
            )
        else:
            if selected_strategies is None:
                selected_strategies = list(strategies.keys())
            for strategy in selected_strategies:
                if strategy in strategies:
                    print(f"***Merging according to <{strategy}>***")
                    run_merge(strategies[strategy])
                else:
                    print(f"***Could not find strategy <{strategy}>***")

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")

        print(stats)
