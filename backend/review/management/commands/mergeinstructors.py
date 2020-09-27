from typing import Callable, Dict, List, Optional

from django.core.management import BaseCommand
from django.db.models.functions import Lower
from tqdm import tqdm

from courses.models import Instructor, Section
from review.models import Review


# Statistic keys
INSTRUCTORS_KEPT = "instructors kept"
INSTRUCTORS_REMOVED = "instructors removed"
SECTIONS_MODIFIED = "sections modified"
REVIEWS_MODIFIED = "reviews modified"
INSTRUCTORS_UNMERGED = "instructors unmerged"


def batch_duplicates(qs, get_prop) -> List[List[Instructor]]:
    """
    Group queryset rows by a property defined in `get_prop()`, return a list-of-lists of groups
    of size > 1.
    :param qs: Queryset to use
    :param get_prop: Function which takes a row and returns a property to group on.
    If get_prop returns None, don't include the row in the groupings.
    :return: List of lists of duplicate rows according to some property.
    """
    rows_by_prop = dict()
    for row in tqdm(qs):
        prop = get_prop(row)
        if prop is None:
            continue
        rows_by_prop.setdefault(prop, []).append(row)
    return [rows for name, rows in rows_by_prop.items() if len(rows) > 1]


def resolve_duplicates(
    duplicate_instructor_groups: List[List[Instructor]], dry_run: bool, stat, force=False
):
    """
    Given a list of list of duplicate instructor groups, resolve the foreign key and many-to-many
    relationships among duplicates to all point to the same instance.

    :param duplicate_instructor_groups: List of lists of duplicate instructors
    e.g. [[a, a, a], [b, b]]
    :param dry_run: If true, just calculate stats without actually modifying the database.
    :param stat: Function to collect statistics.
    :param force: Manually override conflicting user information.
    """
    for instructor_set in tqdm(duplicate_instructor_groups):
        # Find a primary instance in the duplicate set. This should be the instance that is most
        # "complete" -- in the case of instructors, this means that there is a linked user object.
        potential_primary = [inst for inst in instructor_set if inst.user is not None]
        # If no instance has a linked user, just pick one instructor.
        if len(potential_primary) == 0:
            stat(INSTRUCTORS_KEPT, 1)
            primary_instructor = instructor_set[0]
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
                primary_instructor = potential_primary[0]
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
        duplicate_instructors = [
            inst for inst in instructor_set if inst.pk != primary_instructor.pk
        ]
        # Transfer the sections and reviews of all non-primary instances to the primary instance.
        for duplicate_instructor in duplicate_instructors:
            sections = Section.objects.filter(instructors=duplicate_instructor)
            for section in sections:
                stat(SECTIONS_MODIFIED, 1)
                if not dry_run:
                    section.instructors.remove(duplicate_instructor)
                    section.instructors.add(primary_instructor)

            reviews = Review.objects.filter(instructor=duplicate_instructor)
            for review in reviews:
                stat(REVIEWS_MODIFIED, 1)
                if not dry_run:
                    review.instructor = primary_instructor
                    review.save()

            stat(INSTRUCTORS_REMOVED, 1)
            if not dry_run:
                duplicate_instructor.delete()


# Middle Initial ([\w ']+)([a-zA-Z]+\.)([\w ']+)


"""
Strategy definitions. Keys are the strategy name, values are lambdas
which resolve a list of duplicate lists when called. The lambdas are to ensure
lazy evaluation, since we won't necessarily be running all (or any) of the
given strategies.
"""
strategies: Dict[str, Callable[[], List[List[Instructor]]]] = {
    "case-insensitive": lambda: batch_duplicates(
        Instructor.objects.all().annotate(name_lower=Lower("name")).order_by("-updated_at"),
        lambda row: row.name_lower,
    ),
    "pennid": lambda: batch_duplicates(
        Instructor.objects.all().order_by("-updated_at"),
        lambda row: row.user.pk if row.user is not None else None,
    ),
}


class Command(BaseCommand):
    help = """
    Merge duplicate instructor entries through different strategies.

    case-insensitive: Merge instructors with the same name but different cases [O'leary, O'Leary]
    pennid: Merge instructors with the same pennid
    middle-initial: Merge instructors based on firstname and lastname, ignoring middle initials.
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
        group.add_argument("--strategy", "-s", action="append")
        group.add_argument("--all", "-a", action="store_const", const=None, dest="strategies")

    def handle(self, *args, **kwargs):
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

        def run_merge(strat: Callable[[], List[List[Instructor]]], force=False):
            """
            Run a merge pass, printing out helpful messages along the way.
            """
            print("Finding duplicates...")
            duplicates = strat()
            print(f"Found {len(duplicates)} instructors with multiple rows. Merging records...")
            resolve_duplicates(duplicates, dry_run, stat, force)

        if len(manual_merge) > 0:
            print("***Merging records manually***")
            run_merge(lambda: [list(Instructor.objects.filter(pk__in=manual_merge))], force=True)
        else:
            if selected_strategies is None:
                selected_strategies = list(strategies.keys())
            for strategy in selected_strategies:
                if strategy in strategies:
                    print(f"***Merging according to <{strategy}>***")
                    run_merge(strategies[strategy])
                else:
                    print(f"***Could not find strategy <{strategy}>***")

        print(stats)
