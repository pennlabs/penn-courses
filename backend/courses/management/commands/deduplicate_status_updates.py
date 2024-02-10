from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from alert.models import Section, StatusUpdate


def deduplicate_status_updates(semesters: list[str], verbose=False):
    """
    Removes duplicate/redundant status updates from the specified semesters.

    :param semesters: Semesters for which you want to remove duplicate/redundant status updates.
    :param verbose: Whether to print status/progress updates.
    """

    if verbose:
        print(f"Deduplicating status updates for semesters {semesters}...")

    for semester_num, semester in enumerate(semesters):
        with transaction.atomic():
            # We make this command an atomic transaction, so that the database will not
            # be modified unless the entire update for a semester succeeds.

            if verbose:
                print(f"\nProcessing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.")

            num_removed = 0
            for section_id in tqdm(
                Section.objects.filter(course__semester=semester).values_list("id", flat=True),
                disable=(not verbose),
            ):
                last_update = None
                ids_to_remove = []  # IDs of redundant status updates to remove

                for update in StatusUpdate.objects.filter(section_id=section_id).order_by(
                    "created_at"
                ):
                    if (
                        last_update
                        and last_update.old_status == update.old_status
                        and last_update.new_status == update.new_status
                    ):
                        ids_to_remove.append(update.id)
                        continue
                    last_update = update

                num_removed += len(ids_to_remove)
                StatusUpdate.objects.filter(id__in=ids_to_remove).delete()
            print(
                f"Removed {num_removed} duplicate status update objects from semester {semester}."
            )

    if verbose:
        print(f"Finished deduplicating status updates for semesters {semesters}.")


class Command(BaseCommand):
    help = "Remove duplicate/redundant status updates from the given semesters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters for which you want to remove duplicate/redundant
            status updates, i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
            If this argument is omitted, stats are only recomputed for the current semester.
            If you pass "all" to this argument, this script will remove duplicate/redundant
            status updates for all semesters found in Courses in the db.
                """
            ),
            nargs="?",
            default=None,
        )

    def handle(self, *args, **kwargs):
        deduplicate_status_updates(semesters=kwargs["semesters"], verbose=True)
