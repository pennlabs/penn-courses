from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db.models import Q, F
from tqdm import tqdm
from pandas import pd

from alert.management.commands.export_anon_registrations import get_semesters
from courses.models import Topic
from courses.models import Course
from collections import defaultdict
import logging


def should_link_courses(course_a, course_b):
    pass


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


def link_courses_to_topics(semester, cross_walk=None, verbose=False, topics=None):
    """
    Links all courses in the given semester to existing Topics when possible,
    creating new Topics when necessary.
    Args:
        semester: The semester from which to link courses to existing Topics
        cross_walk: Optionally, a path to a crosswalk of manual links between course codes
        verbose: If verbose=True, this script will print its progress and prompt for user input
            upon finding possible (but not definite) links. Otherwise it will run silently and
            log found possible links to Sentry (more appropriate if this function is called
            from an automated cron job like registrarimport).
        topics: You can precompute the Topics used by this script in case you are calling it
            in a loop; the format should be [(most_recent_course, topic), ... for each topic].
    """
    guaranteed_links = get_direct_backlinks_from_cross_walk(cross_walk) if cross_walk else dict()
    if not topics:
        topics = [(t.most_recent, t) for t in Topic.objects.select_related("most_recent").all()]
    full_code_to_topic = {c.full_code: t for c, t in topics}
    for course in Course.objects.filter(
        Q(primary_listing__isnull=True) | Q(primary_listing_id=F("id")), semester=semester
    ).prefetch_related("primary_listing__listing_set"):
        if course.full_code in guaranteed_links:
            old_full_code = guaranteed_links[course.full_code]
            if old_full_code in full_code_to_topic:
                full_code_to_topic[old_full_code][1].add_course(course)
            else:
                Topic.from_course(course)
        else:
            for most_recent, topic in topics:
                should_link = should_link_courses(most_recent, course)
                if should_link == "definitely":
                    topic.add_course(course)
                elif should_link == "maybe":
                    if verbose:
                        print("\n\n============>\n")
                        print(most_recent.full_str())
                        print("\n")
                        print(course.full_str())
                        print("\n<============")
                        prompt = input("Should the above 2 courses be linked? (y/N) ")
                        print("\n\n")
                        if prompt.strip().upper() != "Y":
                            continue
                        topic.add_course(course)
                    else:
                        # Log possible link
                        logging.info(f"Found possible link between {most_recent} and {course}")


class Command(BaseCommand):
    help = "Export test courses, sections, instructors, and reviews data from the given semesters."

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
            NOTE: you should only pass a set of consecutive semesters (or "all"), because this script
            links courses to topics using the most recent course in a topic.
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
                (in the format provided by Susan Collins [squant@isc.upenn.edu] from the data warehouse team; 
                https://bit.ly/3HtqPq3).
                """
            ),
            default="",
        )

    def handle(self, *args, **kwargs):
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if len(semesters) == 0:
            raise ValueError("No semesters provided for course/topic linking.")
        semesters = sorted(semesters)

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

        for i, semester in enumerate(semesters):
            print(f"Processing semester {semester} ({i+1}/{len(semesters)})...")
            link_courses_to_topics(semester, cross_walk=kwargs["cross_walk"], verbose=True)

        print(f"Finished linking courses to topics for semesters {semesters}.")
