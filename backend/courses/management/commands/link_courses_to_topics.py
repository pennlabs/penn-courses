import os
from collections import defaultdict
from textwrap import dedent

import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import F, Max, OuterRef, Q, Subquery
from tqdm import tqdm

from alert.management.commands.export_anon_registrations import get_semesters
from courses.management.commands.merge_topics import (
    ShouldLinkCoursesResponse,
    merge_topics,
    should_link_courses,
)
from courses.models import Course, Topic
from PennCourses.settings.base import S3_client


def get_branches_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping old_full_code to
    a list of the new codes originating from that source, if there are multiple
    (i.e. only in the case of branches).
    """
    branched_links = defaultdict(list)
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        branched_links[old_full_code].append(new_full_code)
    return {
        old_code: new_codes for old_code, new_codes in branched_links.items() if len(new_codes) > 1
    }


def get_direct_backlinks_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping new_full_code->old_full_code,
    ignoring branched links in the crosswalk (a course splitting into multiple new courses).
    """
    guaranteed_links = dict()
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        if old_full_code in guaranteed_links:
            # Ignore branched links
            del guaranteed_links[new_full_code]
        else:
            guaranteed_links[new_full_code] = old_full_code
    return guaranteed_links


def get_topics_and_courses(semester):
    """
    Returns a list of the form [(most_recent_course, topic), ... for each topic]
    where most_recent_course is the most recent primary course in that topic offered
    before or during the given semester.
    """
    max_sem_subq = Subquery(
        Course.objects.filter(topic=OuterRef("topic"), semester__lte=semester)
        .annotate(max_sem=Max("semester"))
        .values("max_sem")
    )
    courses = (
        Course.objects.annotate(max_sem=max_sem_subq)
        .filter(
            Q(primary_listing__isnull=True) | Q(primary_listing_id=F("id")),
            semester__eq=F("max_sem"),
        )
        .select_related("topic")
    )
    return [(course, course.topic) for course in courses]


def link_course_to_topics(course, topics=None, verbose=False):
    """
    Links a given course to existing Topics when possible, creating a new Topic if necessary.
    Args:
        course: A course object to link
        topics: You can precompute the Topics used by this script in case you are calling it
            in a loop; the format should be the same as returned by `get_topics_and_courses`.
        verbose: If verbose=True, this script will print its progress and prompt for user input
            upon finding possible (but not definite) links. Otherwise it will run silently and
            log found possible links to Sentry (more appropriate if this function is called
            from an automated cron job like registrarimport).
    """
    if not topics:
        topics = get_topics_and_courses(course.semester)
    for most_recent, topic in topics:
        if (
            should_link_courses(most_recent, course, verbose=verbose)
            == ShouldLinkCoursesResponse.DEFINITELY
        ):
            topic.add_course(course)
    if not course.topic:
        Topic.from_course(course)


def link_courses_to_topics(semester, guaranteed_links=None, verbose=False):
    """
    Links all courses *without Topics* in the given semester to existing Topics when possible,
    creating new Topics when necessary.
    Args:
        semester: The semester for which to link courses to existing Topics
        guaranteed_links: Optionally, a `guaranteed_links` dict returned by
            `get_direct_backlinks_from_cross_walk`.
        verbose: If verbose=True, this script will print its progress and prompt for user input
            upon finding possible (but not definite) links. Otherwise it will run silently and
            log found possible links to Sentry (more appropriate if this function is called
            from an automated cron job like registrarimport).
    """
    guaranteed_links = guaranteed_links or dict()
    topics = get_topics_and_courses(semester)
    full_code_to_topic = {c.full_code: t for c, t in topics}
    iterator_wrapper = tqdm if verbose else lambda i: i
    for course in iterator_wrapper(
        Course.objects.filter(
            Q(primary_listing__isnull=True) | Q(primary_listing_id=F("id")),
            semester=semester,
            topic__isnull=True,
        ).prefetch_related("primary_listing__listing_set")
    ):
        if course.full_code in guaranteed_links:
            old_full_code = guaranteed_links[course.full_code]
            if old_full_code in full_code_to_topic:
                full_code_to_topic[old_full_code][1].add_course(course)
            else:
                Topic.from_course(course)
        else:
            link_course_to_topics(course, topics=topics, verbose=verbose)


class Command(BaseCommand):
    help = (
        "This script populates the Topic table in the database, using a combination of an "
        "optionally provided crosswalk, heuristics, and user input to merge courses with different "
        "codes into the same Topic when appropriate. This script is only intended to be run "
        "once, right after the Topic model is added to the codebase."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters from which you want to link courses with topics,
            i.e. "2019C,2020A,2020B,2020C" for fall 2019, spring 2020, summer 2020, and fall 2020.
            If you pass "all" to this argument, this script will export all status updates.
            NOTE: you should only pass a set of consecutive semesters (or "all"), because
            this script links courses to topics using the most recent course in a topic.
                """
            ),
            default="",
        )
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
            "-s3", "--s3_bucket", help="download crosswalk from specified s3 bucket."
        )

    def handle(self, *args, **kwargs):
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if not semesters:
            return "ERROR: no semesters provided for course/topic linking"
        semesters = sorted(semesters)
        cross_walk_src = kwargs["cross_walk"]
        s3_bucket = kwargs["s3_bucket"]

        # Check that no semesters are skipped in the ordering
        if not all(
            (ord(prev[4]) == ord(next[4]) - 1 and prev[:4] == next[:4])
            or (
                prev[4].lower() == "c"
                and next[4].lower() == "a"
                and int(prev[:4]) == int(next[:4]) - 1
            )
            for prev, next in zip(semesters[:-1], semesters[1:])
        ):
            return "ERROR: please specify a set of consecutive semesters, or 'all'"

        if cross_walk_src and s3_bucket:
            fp = "/tmp/" + cross_walk_src
            print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
            S3_client.download_file(s3_bucket, cross_walk_src, fp)
            cross_walk_src = fp

        guaranteed_links = (
            get_direct_backlinks_from_cross_walk(cross_walk_src) if cross_walk_src else dict()
        )

        if s3_bucket:
            # Remove temporary file
            os.remove(cross_walk_src)

        merge_topics(guaranteed_links=guaranteed_links, verbose=True)

        for i, semester in enumerate(semesters):
            print(f"Processing semester {semester} ({i+1}/{len(semesters)})...")
            link_courses_to_topics(semester, guaranteed_links=guaranteed_links, verbose=True)

        print(f"Finished linking courses to topics for semesters {semesters}.")
