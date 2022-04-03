import os
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from tqdm import tqdm

from alert.management.commands.recomputestats import all_semesters
from courses.management.commands.merge_topics import (
    ShouldLinkCoursesResponse,
    get_direct_backlinks_from_cross_walk,
    should_link_courses,
)
from courses.models import Course, Topic
from PennCourses.settings.base import S3_client


def get_topics_and_courses(semester):
    """
    Returns a list of the form [(topic, most_recent), ... for each topic]
    """
    return [
        (topic, topic.most_recent) for topic in Topic.objects.prefetch_related("most_recent").all()
    ]


def link_course_to_topics(course, topics=None, verbose=False, ignore_inexact=False):
    """
    Links a given course to existing Topics when possible, creating a new Topic if necessary.

    :param course: A course object to link
    :param topics: You can precompute the Topics used by this script in case you are calling it
        in a loop; the format should be the same as returned by `get_topics_and_courses`.
    :param verbose: If verbose=True, this script will print its progress and prompt for user input
        upon finding possible (but not definite) links. Otherwise it will run silently and
        log found possible links to Sentry (more appropriate if this function is called
        from an automated cron job like registrarimport).
    :param ignore_inexact: If ignore_inexact=True, will only ever merge if two courses
        are exactly matching as judged by `same_course`. `ignore_inexact` means
        the user will not be prompted and that there will never be logging.
        Corresponds to never checking the similarity of two courses using `similar_courses`.
    """
    if topics is None:
        topics = get_topics_and_courses(course.semester)
    for topic, most_recent in topics:
        if (
            should_link_courses(most_recent, course, verbose=verbose, ignore_inexact=ignore_inexact)
            == ShouldLinkCoursesResponse.DEFINITELY
        ):
            topic.add_course(course)
    if not course.topic:
        Topic.from_course(course)


def link_courses_to_topics(semester, guaranteed_links=None, verbose=False, ignore_inexact=False):
    """
    Links all courses *without Topics* in the given semester to existing Topics when possible,
    creating new Topics when necessary.

    :param semester: The semester for which to link courses to existing Topics
    :param guaranteed_links: Optionally, a `guaranteed_links` dict returned by
        `get_direct_backlinks_from_cross_walk`.
    :param verbose: If verbose=True, this script will print its progress and prompt for user input
        upon finding possible (but not definite) links. Otherwise it will run silently and
        log found possible links to Sentry (more appropriate if this function is called
        from an automated cron job like registrarimport).
    :param ignore_inexact: If ignore_inexact=True, will only ever merge if two courses
        are exactly matching as judged by `same_course`. `ignore_inexact` means
        the user will not be prompted and that there will never be logging.
        Corresponds to never checking the similarity of two courses using `similar_courses`.
    """
    guaranteed_links = guaranteed_links or dict()
    topics = get_topics_and_courses(semester)
    full_code_to_topic = {c.full_code: t for t, c in topics if c.full_code}
    for course in tqdm(
        Course.objects.filter(
            Q(primary_listing__isnull=True) | Q(primary_listing_id=F("id")),
            semester=semester,
            topic__isnull=True,
        ).select_related("primary_listing"),
        disable=(not verbose),
    ):
        old_full_code = guaranteed_links.get(course.full_code)
        if old_full_code in full_code_to_topic:
            full_code_to_topic[old_full_code].add_course(course)
        else:
            link_course_to_topics(
                course, topics=topics, verbose=verbose, ignore_inexact=ignore_inexact
            )


class Command(BaseCommand):
    help = (
        "This script populates the Topic table in the database, using a combination of an "
        "optionally provided crosswalk, heuristics, and user input to merge courses with different "
        "codes into the same Topic when appropriate. This script is only intended to be run "
        "once, right after the Topic model is added to the codebase. "
        "NOTE: this script will delete any existing Topics before repopulating."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cross-walk",
            type=str,
            help=dedent(
                """
                Optionally specify a path to a crosswalk specifying links between course codes
                (in the format provided by Susan Collins [squant@isc.upenn.edu] from
                the data warehouse team; https://bit.ly/3HtqPq3).
                """
            ),
            default="",
        )
        parser.add_argument(
            "-s3", "--s3-bucket", help="download crosswalk from specified s3 bucket."
        )
        parser.add_argument(
            "--ignore-inexact",
            action="store_true",
            help=dedent(
                """
                Optionally, ignore inexact matches between courses (ie where there is no match
                between course a's code and the codes of all cross listings of course b (including
                course b) AND there is no cross walk entry. Corresponds to never checking
                the similarity of two courses using `similar_courses`.
                """
            ),
        )

    def handle(self, *args, **kwargs):
        semesters = sorted(list(all_semesters()))
        cross_walk_src = kwargs["cross_walk"]
        s3_bucket = kwargs["s3_bucket"]
        ignore_inexact = kwargs["ignore_inexact"]

        if cross_walk_src and s3_bucket:
            fp = "/tmp/" + cross_walk_src
            print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
            S3_client.download_file(s3_bucket, cross_walk_src, fp)
            cross_walk_src = fp

        guaranteed_links = (
            get_direct_backlinks_from_cross_walk(cross_walk_src) if cross_walk_src else dict()
        )

        if cross_walk_src and s3_bucket:
            # Remove temporary file
            os.remove(cross_walk_src)

        print(
            "This script is atomic, meaning either all Topic links will be added to the database, "
            "or otherwise if an error is encountered, all changes will be rolled back and the "
            "database will remain as it was before the script was run."
        )

        with transaction.atomic():
            to_delete = Topic.objects.all()
            prompt = input(
                f"This script will delete all Topic objects ({to_delete.count()} total). "
                "Proceed? (y/N) "
            )
            if prompt.strip().upper() != "Y":
                return
            to_delete.delete()
            print("Linking courses to topics.")
            for i, semester in enumerate(semesters):
                print(f"Processing semester {semester} ({i+1}/{len(semesters)})...")
                link_courses_to_topics(
                    semester,
                    guaranteed_links=guaranteed_links,
                    verbose=True,
                    ignore_inexact=ignore_inexact,
                )

        print(
            f"Finished linking courses to topics for semesters {semesters}."
            f"(created {Topic.objects.all().count()} topics)."
        )
