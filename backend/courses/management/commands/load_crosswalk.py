import os
from collections import defaultdict

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course
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

    with transaction.atomic():
        roots = (
            Course.objects.filter(full_code__in=crosswalk.keys())
            .order_by("semester")
            .select_related("topic")
        )
        # Take maximum semester course matching child code
        root_to_topic = {root.full_code: root.topic for root in roots if root.topic}

        children = (
            Course.objects.filter(
                full_code__in=[c for children in crosswalk.values() for c in children]
            )
            .order_by("-semester")
            .select_related("topic")
        )
        # Take minimum semester course matching child code
        child_to_topic = {child.full_code: child.topic for child in children if child.topic}

        num_merges = 0
        num_branch_updates = 0
        num_missing_roots = 0
        num_missing_children = 0

        for root_course, children in tqdm(crosswalk.items()):
            if root_course not in root_to_topic:
                num_missing_roots += 1
                if print_missing:
                    print(f"Root course {root_course} not found in db")
                continue
            root_topic = root_to_topic[root_course]
            child_topics = set()
            force_branch = False
            for child_code in children:
                if child_code not in child_to_topic:
                    num_missing_children += 1
                    if print_missing:
                        print(f"Child course {child_code} not found in db")
                    force_branch = True  # unknown future course
                else:
                    child_topics.add(child_to_topic[child_code])
            if len(child_topics) == 1 and not force_branch:
                child_topic = child_topics.pop()
                if child_topic.branched_from:
                    child_topic.branched_from = None
                    child_topic.save()
                if root_topic != child_topic:
                    root_topic.merge_with(child_topic)
                    num_merges += 1
            else:
                for child_topic in child_topics:
                    if child_topic.branched_from != root_topic:
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
        clear_cache()
