import logging
from collections import defaultdict
from enum import Enum, auto
from textwrap import dedent

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.course_similarity.heuristics import (
    description_rejection_heuristics,
    lev_divided_by_avg_title_length,
    semantic_similarity,
    title_rejection_heuristics,
)
from courses.models import Topic


def load_crosswalk_links(cross_walk):
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


def get_branches_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping old_full_code to
    a list of the new codes originating from that source, if there are multiple
    (i.e. only in the case of branches).
    """
    return {
        old_code: new_codes
        for old_code, new_codes in load_crosswalk_links(cross_walk).items()
        if len(new_codes) > 1
    }


def get_direct_backlinks_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping new_full_code->old_full_code,
    ignoring branched links in the crosswalk (a course splitting into multiple new courses).
    """
    return {
        old_code: new_codes[0]
        for old_code, new_codes in load_crosswalk_links(cross_walk).items()
        if len(new_codes) == 1
    }


def prompt_for_link_multiple(courses, extra_newlines=True):
    """
    Prompts the user to confirm or reject a possible link between multiple courses.
    Returns a boolean representing whether the courses should be linked.
    """
    print("\n\n============>\n")
    print("\n".join(course.full_str() for course in courses))
    print("\n<============")
    prompt = input(f"Should the above {len(courses)} courses be linked? (y/N) ")
    if extra_newlines:
        print("\n\n")
    return prompt.strip().upper() == "Y"


def prompt_for_link(course1, course2):
    """
    Prompts the user to confirm or reject a possible link between courses.
    Returns a boolean representing whether the courses should be linked.
    """
    return prompt_for_link_multiple([course1, course2])


def same_course(course_a, course_b):
    return course_a.full_code == course_b.full_code or any(
        course_ac.full_code == course_b.full_code
        for course_ac in (course_a.primary_listing or course_a).listing_set.all()
    )


def similar_courses(course_a, course_b):
    title_a, title_b = course_a.title.strip().lower(), course_b.title.strip().lower()
    if (
        not title_rejection_heuristics(title_a, title_b)
        and lev_divided_by_avg_title_length(title_a, title_b) < 0.2
    ):
        return True
    desc_a, desc_b = course_a.description.strip().lower(), course_b.description.strip().lower()
    if (
        not description_rejection_heuristics(desc_a, desc_b)
        and semantic_similarity(desc_a, desc_b) > 0.7
        and semantic_similarity(desc_a, desc_b) > 0.7
    ):
        return True
    return False


class ShouldLinkCoursesResponse(Enum):
    DEFINITELY = auto()
    MAYBE = auto()
    NO = auto()


def should_link_courses(course_a, course_b, verbose=True, ignore_inexact=False):
    """
    Checks if the two courses should be linked, based on information about those
    courses stored in our database. Prompts for user input in the case of possible links,
    if in verbose mode (otherwise just logs possible links). If in `ignore_inexact` mode,
    completely skips any course merges that are inexact (ie, rely on `similar_courses`),
    and therefore will neither prompt for user input nor log.
    Returns a response in the form of a ShouldLinkCoursesResponse enum.
    """
    if same_course(course_a, course_b):
        return ShouldLinkCoursesResponse.DEFINITELY
    elif course_a.semester == course_b.semester:
        return ShouldLinkCoursesResponse.NO
    elif (course_a.code < "5000") != (course_b.code < "5000"):
        return ShouldLinkCoursesResponse.NO
    elif (not ignore_inexact) and similar_courses(course_a, course_b):
        if verbose:
            return (
                ShouldLinkCoursesResponse.DEFINITELY
                if prompt_for_link(course_a, course_b)
                else ShouldLinkCoursesResponse.NO
            )
        else:
            # Log possible link
            logging.info(f"Found possible link between {course_a} and {course_b}")
            return ShouldLinkCoursesResponse.MAYBE
    return ShouldLinkCoursesResponse.NO


def merge_topics(verbose=False, ignore_inexact=False):
    """
    Finds and merges Topics that should be merged.

    :param verbose: If verbose=True, this script will print its progress and prompt for user input
        upon finding possible (but not definite) links. Otherwise it will run silently and
        log found possible links to Sentry (more appropriate if this function is called
        from an automated cron job like registrarimport).
    :param ignore_inexact: If ignore_inexact=True, will only ever merge if two courses
        are exactly matching as judged by `same_course`. `ignore_inexact` means
        the user will not be prompted and that there will never be logging.
        Corresponds to never checking the similarity of two courses using `similar_courses`.
    """
    if verbose:
        print("Merging topics")
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
                        should_link_courses(
                            last, course, verbose=verbose, ignore_inexact=ignore_inexact
                        )
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


def manual_merge(topic_ids):
    invalid_ids = [i for i in topic_ids if not i.isdigit()]
    if invalid_ids:
        print(
            f"The following topic IDs are invalid (non-integer):\n{invalid_ids}\n" "Aborting merge."
        )
        return
    topic_ids = [int(i) for i in topic_ids]
    topics = Topic.objects.filter(id__in=topic_ids).prefetch_related("courses")
    found_ids = topics.values_list("id", flat=True)
    not_found_ids = list(set(topic_ids) - set(found_ids))
    if not_found_ids:
        print(f"The following topic IDs were not found:\n{not_found_ids}\nAborting merge.")
        return
    courses = [course for topic in topics for course in topic.courses.all()]
    if not prompt_for_link_multiple(courses, extra_newlines=False):
        print("Aborting merge.")
        return
    with transaction.atomic():
        topic = topics[0]
        for topic2 in topics[1:]:
            topic = topic.merge_with(topic2)
    print(f"Successfully merged {len(topics)} topics into: {topic}.")


class Command(BaseCommand):
    help = (
        "This script uses a combination of heuristics and user input "
        "to merge Topics in the database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-t",
            "--topic-ids",
            nargs="*",
            help=dedent(
                """
            Optionally, specify a (space-separated) list of Topic IDs to merge into a single topic.
            You can find Topic IDs from the django admin interface (either by searching through
            Topics or by following the topic field from a course entry).
            If this argument is omitted, the script will automatically detect merge opportunities
            among all Topics, prompting the user for confirmation before merging in each case.
            """
            ),
            required=False,
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
        topic_ids = set(kwargs["topic_ids"])
        ignore_inexact = kwargs["ignore_inexact"]

        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        if topic_ids:
            manual_merge(topic_ids)
            return

        with transaction.atomic():
            merge_topics(verbose=True, ignore_inexact=ignore_inexact)
