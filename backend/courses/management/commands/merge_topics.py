import logging
from enum import Enum, auto
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.course_similarity.heuristics import (
    description_rejection_heuristics,
    title_rejection_heuristics,
)
from courses.management.commands.load_crosswalk import load_crosswalk
from courses.management.commands.reset_topics import fill_topics
from courses.models import Topic
from review.management.commands.clearcache import clear_cache


def prompt_for_link_topics(topics):
    """
    Prompts the user to confirm or reject a merge of topics.
    Returns a boolean representing whether the topics should be merged.
    """
    for topic in topics:
        print(f"\n============> {topic}:\n")
        print("\n------\n".join(course.full_str() for course in topic.courses.all()))
        print("\n<============")
    prompt = input(f"Should the above {len(topics)} topics be merged? (y/N) ")
    return prompt.strip().upper() == "Y"


def prompt_for_link(course1, course2):
    """
    Prompts the user to confirm or reject a possible link between courses.
    Returns a boolean representing whether the courses should be linked.
    """
    print("\n\n============>\n")
    course1.full_str()
    print("------")
    course2.full_str()
    print("\n<============")
    prompt = input("Should the above 2 courses be linked? (y/N) ")
    print("\n\n")
    return prompt.strip().upper() == "Y"


def same_course(course_a, course_b):
    return any(
        course_bc.full_code == course_a.primary_listing.full_code
        for course_bc in course_b.primary_listing.listing_set.all()
    )


def similar_courses(course_a, course_b):
    title_a, title_b = course_a.title.strip().lower(), course_b.title.strip().lower()
    if not title_rejection_heuristics(title_a, title_b):
        return True
    desc_a, desc_b = course_a.description.strip().lower(), course_b.description.strip().lower()
    if not description_rejection_heuristics(desc_a, desc_b):
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
    topics = set(
        Topic.objects.select_related("most_recent")
        .prefetch_related(
            "courses",
            "courses__primary_listing",
            "courses__primary_listing__listing_set",
        )
        .all()
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
                if topic.most_recent.semester == topic2.most_recent.semester:
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
    topics = (
        Topic.objects.filter(id__in=topic_ids)
        .select_related("most_recent")
        .prefetch_related("courses")
    )
    found_ids = topics.values_list("id", flat=True)
    not_found_ids = list(set(topic_ids) - set(found_ids))
    if not_found_ids:
        print(f"The following topic IDs were not found:\n{not_found_ids}\nAborting merge.")
        return
    if not prompt_for_link_topics(topics):
        print("Aborting merge.")
        return
    topic = Topic.merge_all(topics)
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
        topic_ids = set(kwargs["topic_ids"] or [])
        ignore_inexact = kwargs["ignore_inexact"]

        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        if topic_ids:
            manual_merge(topic_ids)
        else:
            with transaction.atomic():
                fill_topics(verbose=True)
                merge_topics(verbose=True, ignore_inexact=ignore_inexact)
                load_crosswalk(verbose=True)

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
