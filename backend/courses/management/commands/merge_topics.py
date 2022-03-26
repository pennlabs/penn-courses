import logging
from enum import Enum, auto

from tqdm import tqdm

from courses.models import Topic


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


def should_link_courses(course_a, course_b, verbose=True):
    """
    Checks if the two courses should be linked, based on information about those
    courses stored in our database. Prompts for user input in the case of possible links,
    if in verbose mode (otherwise just logs possible links).
    Returns a response in the form of a ShouldLinkCoursesResponse enum.
    """
    if course_a.full_code == course_b.full_code or course_a.primary_listing and any(
        course_ac.full_code == course_b.full_code for course_ac in course_a.primary_listing.listing_set
    ):
        return ShouldLinkCoursesResponse.DEFINITELY
    elif course_a.semester == course_b.semester:
        return ShouldLinkCoursesResponse.NO
    elif False:  # TODO
        # If title is same or (title is similar and description is similar
        # have a fairly low threshold for similarity)
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
    topics = set(Topic.objects.prefetch_related("courses", "courses__crosslistings").all())
    merge_count = 0

    iterator_wrapper = tqdm if verbose else lambda i: i
    for topic in iterator_wrapper(list(topics)):
        if topic not in topics:
            continue
        keep_linking = True
        while keep_linking:
            keep_linking = False
            for topic2 in topics:
                merged_courses = list(topic.courses) + list(topic2.courses)
                merged_courses.sort(key=lambda c: (c.semester, c.topic_id))
                course_links = []
                last = merged_courses[0]
                for course in merged_courses[1:]:
                    if last.topic_id != course.topic_id:
                        course_links.append((last, course))
                    last = course
                if any(
                    course_a.semester == course_b.semester
                    and not (
                        course_a.full_code == course_b.full_code
                        or any(
                            course_ac.full_code == course_b.full_code
                            for course_ac in course_a.crosslistings
                        )
                    )
                    for course_a, course_b in course_links
                ):
                    continue
                should_link = True
                for last, course in course_links:
                    if (
                        should_link_courses(last, course, verbose=verbose)
                        != ShouldLinkCoursesResponse.DEFINITELY
                    ):
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
