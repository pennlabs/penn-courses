import logging
import os
from collections import defaultdict
from enum import Enum, auto
from textwrap import dedent

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Topic
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
    links = defaultdict(list)
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        links[old_full_code].append(new_full_code)
    return {old_code: new_codes[0] for old_code, new_codes in links.items() if len(new_codes) == 1}


class ShouldLinkCoursesResponse(Enum):
    DEFINITELY = auto()
    MAYBE = auto()
    NO = auto()


def prompt_for_link(course1, course2):
    """
    Prompts the user to confirm or reject a possible link between courses.
    Returns a boolean representing whether the courses should be linked.
    """
    print("\n\n============>\n")
    print(course1.full_str())
    print("\n")
    print(course2.full_str())
    print("\n<============")
    prompt = input("Should the above 2 courses be linked? (y/N) ")
    print("\n\n")
    return prompt.strip().upper() == "Y"


def same_course(course_a, course_b):
    return course_a.full_code == course_b.full_code or any(
        course_ac.full_code == course_b.full_code
        for course_ac in (course_a.primary_listing or course_a).listing_set.all()
    )


def should_link_courses(course_a, course_b, verbose=True):
    """
    Checks if the two courses should be linked, based on information about those
    courses stored in our database. Prompts for user input in the case of possible links,
    if in verbose mode (otherwise just logs possible links).
    Returns a response in the form of a ShouldLinkCoursesResponse enum.
    """
    if same_course(course_a, course_b):
        return ShouldLinkCoursesResponse.DEFINITELY
    elif course_a.semester == course_b.semester:
        return ShouldLinkCoursesResponse.NO
    elif (course_a.code < "5000") != (course_b.code < "5000"):
        return ShouldLinkCoursesResponse.NO
    elif False:  # TODO
        # If title is same or (title is similar and description is similar
        # have a fairly low threshold for similarity)
        # TODO: search for "topics vary" in description, say no
        if verbose and prompt_for_link(course_a, course_b):
            return ShouldLinkCoursesResponse.DEFINITELY
        if not verbose:
            # Log possible link
            logging.info(f"Found possible link between {course_a} and {course_b}")
        return ShouldLinkCoursesResponse.MAYBE
    return ShouldLinkCoursesResponse.NO


def merge_topics(guaranteed_links=None, verbose=False):
    """
    Finds and merges Topics that should be merged.
    Args:
        guaranteed_links: Optionally, a `guaranteed_links` dict returned by
            `get_direct_backlinks_from_cross_walk`.
        verbose: If verbose=True, this script will print its progress and prompt for user input
            upon finding possible (but not definite) links. Otherwise it will run silently and
            log found possible links to Sentry (more appropriate if this function is called
            from an automated cron job like registrarimport).
    """
    if verbose:
        print("Merging topics")
    guaranteed_links = guaranteed_links or dict()
    if verbose:
        print("Loading topics and courses from db (this may take a while)...")
    topics = set(
        Topic.objects.prefetch_related(
            "courses",
            "courses__listing_set",
            "courses__primary_listing",
            "courses__primary_listing__listing_set",
        ).all()
    )
    dont_link = set()
    merge_count = 0

    for topic in tqdm(list(topics), disable=(not verbose)):
        if topic not in topics:
            continue
        keep_linking = True
        while keep_linking:
            keep_linking = False
            for topic2 in topics:
                if topic == topic2:
                    continue
                merged_courses = list(topic.courses.all()) + list(topic2.courses.all())
                merged_courses.sort(key=lambda c: (c.semester, c.topic_id))
                course_links = []
                last = merged_courses[0]
                for course in merged_courses[1:]:
                    if last.topic_id != course.topic_id:
                        course_links.append((last, course))
                    last = course
                if any(
                    course_a.semester == course_b.semester and not same_course(course_a, course_b)
                    for course_a, course_b in course_links
                ):
                    continue
                should_link = True
                for last, course in course_links:
                    if (last, course) in dont_link or (
                        should_link_courses(last, course, verbose=verbose)
                        != ShouldLinkCoursesResponse.DEFINITELY
                    ):
                        dont_link.add((last, course))
                        should_link = False
                        break
                if should_link:
                    topics.remove(topic)
                    topics.remove(topic2)
                    topic = topic.merge_with(topic2)
                    topics.add(topic)
                    merge_count += 1
                    keep_linking = True
                    break

    if verbose:
        print(f"Finished merging topics (performed {merge_count} merges).")


class Command(BaseCommand):
    help = (
        "This script uses a combination of an optionally provided crosswalk, heuristics, "
        "and user input to merge Topics in the database."
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
            "-s3", "--s3_bucket", help="download crosswalk from specified s3 bucket."
        )

    def handle(self, *args, **kwargs):
        cross_walk_src = kwargs["cross_walk"]
        s3_bucket = kwargs["s3_bucket"]

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
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        with transaction.atomic():
            merge_topics(guaranteed_links=guaranteed_links, verbose=True)
