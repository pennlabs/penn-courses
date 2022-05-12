import os
from collections import defaultdict

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course, Topic
from PennCourses.settings.base import XWALK_S3_BUCKET, XWALK_SRC, S3_client
from review.management.commands.clearcache import clear_cache


def get_crosswalk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping old_full_code to
    a list of the new codes originating from that source.
    """
    links = defaultdict(list)
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        links[old_full_code].append(new_full_code)
    return links


def get_crosswalk_s3(verbose=False):
    """
    From the crosswalk crosswalk from settings/base.py, generate a dict mapping
    old_full_code to a list of the new codes originating from that source.
    """
    fp = "/tmp/" + XWALK_SRC
    if verbose:
        print(f"downloading crosswalk from s3://{XWALK_S3_BUCKET}/{XWALK_SRC}")
    S3_client.download_file(XWALK_S3_BUCKET, XWALK_SRC, fp)

    crosswalk = get_crosswalk(fp)

    # Remove temporary file
    os.remove(fp)

    return crosswalk


def load_crosswalk(print_missing=False, verbose=False):
    """
    Loads the crosswalk from settings/base.py, updating branched_from fields
    and merging Topics as appropriate.

    :param print_missing: If True, prints courses involved in crosswalk links that were
        not found in the database.
    :param verbose: A flag indicating whether this script should print its progress.
    """
    crosswalk = get_crosswalk_s3(verbose=verbose)

    if verbose:
        print("Loading crosswalk.")

    num_merges = 0
    num_branch_updates = 0
    num_missing_roots = 0
    num_missing_children = 0

    with transaction.atomic():
        Topic.objects.all().update(branched_from=None)
        for root_course_code, children_codes in tqdm(crosswalk.items()):
            root_course = (
                Course.objects.filter(full_code=root_course_code)
                .order_by("-semester")
                .select_related("topic")
                .first()
            )
            if not root_course:
                num_missing_roots += 1
                if print_missing:
                    print(f"Root course {root_course} not found in db")
                continue
            root_topic = root_course.topic
            assert root_topic, f"Root course {root_course} has no topic"

            children = (
                Course.objects.filter(
                    full_code__in=children_codes, semester__gt=root_course.semester
                )
                .order_by("-semester")
                .select_related("topic")
            )
            # Take minimum semester course (after root course semester) matching child code
            child_to_topic = {child.full_code: child.topic for child in children}
            for child in {child.full_code: child for child in children}.values():
                assert child.topic, f"Child course {child} of root {root_course} has no topic"
            child_topics = set(child_to_topic.values())
            missing_codes = set(children_codes) - set(child_to_topic.keys())

            for child_code in missing_codes:
                num_missing_children += 1
                if print_missing:
                    print(f"Child course {child_code} not found in db")

            if len(child_topics) == 1 and not missing_codes:
                child_topic = child_topics.pop()
                if child_topic.branched_from:
                    child_topic.branched_from = None
                    child_topic.save()
                if root_topic != child_topic:
                    root_topic.merge_with(child_topic)
                    num_merges += 1
            else:
                for child_topic in child_topics:
                    if root_topic not in [child_topic, child_topic.branched_from]:
                        num_branch_updates += 1
                        child_topic.branched_from = root_topic
                        child_topic.save()

    if verbose:
        print(f"Performed {num_merges} Topic merges.")
        print(f"Added branches, updating the branched_from field of {num_branch_updates} Topics.")
        print(f"{num_missing_roots}/{len(crosswalk)} roots not found in db")
        print(
            f"{num_missing_children}/{sum(len(c) for c in crosswalk.values())} "
            "children not found in db"
        )


class Command(BaseCommand):
    help = (
        "This script loads the crosswalk from settings/base.py, updating "
        "branched_from fields and merging Topics as appropriate."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--print_missing",
            action="store_true",
            help="Print out all missing roots and children.",
        )

    def handle(self, *args, **kwargs):
        load_crosswalk(print_missing=kwargs["print_missing"], verbose=True)

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
