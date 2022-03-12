import os
from textwrap import dedent

from django.core.management.base import BaseCommand

from courses.management.commands.link_courses_to_topics import get_branches_from_cross_walk
from courses.models import Course, Topic
from PennCourses.settings.base import S3_client


def load_topic_branches(branches, verbose=False):
    """
    Loads specified topic branches into the branched_from field of the Topic model.
    Args:
        branches: A dict specifying topic branches, in the form returned by
            `get_direct_backlinks_from_cross_walk`
        verbose: If verbose=True, this script will print its progress.
            Otherwise it will run silently.
    """
    if verbose:
        print("Loading branches into the db.")

    roots = Course.objects.filter(full_code__in=branches.keys()).select_related("topic")
    root_to_topic = {root.full_code: root.topic for root in roots if root.topic is not None}
    children = Course.objects.filter(
        full_code__in=[c for children in branches.values() for c in children]
    )
    child_to_topic = {child.full_code: child.topic for child in children if child.topic is not None}
    topics_to_save = dict()

    for branched_from_code, children in branches.items():
        if branched_from_code not in root_to_topic:
            if verbose:
                print(f"Root course {branched_from_code} not found in db")
            continue
        branched_from = root_to_topic[branched_from_code]
        for child_code in children:
            if child_code not in child_to_topic:
                if verbose:
                    print(f"Child course {child_code} not found in db")
                continue
            child_topic = child_to_topic[child_code]
            child_topic.branched_from = branched_from
            topics_to_save[child_topic.id] = child_topic

    if topics_to_save:
        Topic.objects.bulk_update(topics_to_save, ["branched_from"])

    if verbose:
        print(f"Loaded {len(topics_to_save)} branches into the db.")


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
            default="",
        )
        parser.add_argument(
            "-s3", "--s3_bucket", help="download crosswalk from specified s3 bucket."
        )

    def handle(self, *args, **kwargs):
        cross_walk_src = args[0]
        s3_bucket = kwargs["s3_bucket"]

        if cross_walk_src and s3_bucket:
            fp = "/tmp/" + cross_walk_src
            print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
            S3_client.download_file(s3_bucket, cross_walk_src, fp)
            cross_walk_src = fp

        branches = get_branches_from_cross_walk(cross_walk_src)

        if s3_bucket:
            # Remove temporary file
            os.remove(cross_walk_src)

        load_topic_branches(branches, verbose=True)
