import os
from textwrap import dedent

from django.core.management.base import BaseCommand

from courses.management.commands.merge_topics import get_branches_from_cross_walk
from courses.models import Course, Topic
from PennCourses.settings.base import S3_client
from review.management.commands.clearcache import clear_cache


def load_topic_branches(branches, print_missing=False, verbose=False):
    """
    Loads specified topic branches into the branched_from field of the Topic model.

    :param branches: A dict specifying topic branches, in the form returned by
        `get_branches_from_cross_walk`.
    :param print_missing: If True, prints courses involved in branches that were
        not found in the database.
    :param verbose: A flag indicating whether this script should print its progress.
    """
    if verbose:
        print("Loading branches into the db.")

    roots = (
        Course.objects.filter(full_code__in=branches.keys())
        .order_by("semester")
        .select_related("topic")
    )
    # Take maximum semester course matching child code
    root_to_topic = {root.full_code: root.topic for root in roots if root.topic}

    children = (
        Course.objects.filter(full_code__in=[c for children in branches.values() for c in children])
        .order_by("-semester")
        .select_related("topic")
    )
    # Take minimum semester course matching child code
    child_to_topic = {child.full_code: child.topic for child in children if child.topic}

    topics_to_save = dict()

    num_merges = 0
    num_missing_roots = 0
    num_missing_children = 0

    for branched_from_code, children in branches.items():
        if branched_from_code not in root_to_topic:
            num_missing_roots += 1
            if print_missing:
                print(f"Root course {branched_from_code} not found in db")
            continue
        branched_from = root_to_topic[branched_from_code]
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
            if branched_from != child_topic:
                branched_from.merge_with(child_topic)
                num_merges += 1
        else:
            for child_topic in child_topics:
                child_topic.branched_from = branched_from
                topics_to_save[child_topic.id] = child_topic

    if topics_to_save:
        Topic.objects.bulk_update(topics_to_save.values(), ["branched_from"])

    if verbose:
        print(f"Added branches, updating the branched_from field of {len(topics_to_save)} topics.")
        print(f"Performed {num_merges} merges.")
        print(f"{num_missing_roots}/{len(branches)} roots not found in db")
        print(
            f"{num_missing_children}/{sum(len(c) for c in branches.values())} "
            "children not found in db"
        )


def load_topic_branches_s3(s3_bucket, cross_walk_src, print_missing=False, verbose=False):
    fp = "/tmp/" + cross_walk_src
    if verbose:
        print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
    S3_client.download_file(s3_bucket, cross_walk_src, fp)
    cross_walk_src = fp

    branches = get_branches_from_cross_walk(cross_walk_src)

    # Remove temporary file
    os.remove(cross_walk_src)

    load_topic_branches(branches, print_missing=print_missing, verbose=verbose)


class Command(BaseCommand):
    help = (
        "This script loads topic branches from a crosswalk into the Topic model "
        "of our database (populating the branched_from field)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "cross-walk",
            type=str,
            help=dedent(
                """
                Specify a path to a crosswalk specifying links between course codes
                (in the format provided by Susan Collins [squant@isc.upenn.edu] from
                the data warehouse team; https://bit.ly/3HtqPq3).
                """
            ),
        )
        parser.add_argument(
            "-s3", "--s3-bucket", help="download crosswalk from specified s3 bucket."
        )
        parser.add_argument(
            "--print_missing",
            action="store_true",
            help="Print out all missing roots and children.",
        )

    def handle(self, *args, **kwargs):
        cross_walk_src = kwargs["cross-walk"]
        s3_bucket = kwargs["s3_bucket"]
        print_missing = kwargs["print_missing"]

        if s3_bucket:
            fp = "/tmp/" + cross_walk_src
            print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
            S3_client.download_file(s3_bucket, cross_walk_src, fp)
            cross_walk_src = fp

        branches = get_branches_from_cross_walk(cross_walk_src)

        if s3_bucket:
            # Remove temporary file
            os.remove(cross_walk_src)

        load_topic_branches(branches, print_missing=print_missing, verbose=True)

        print("Clearing cache")
        clear_cache()
