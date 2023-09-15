from pprint import pprint
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Exists, OuterRef, Count

from alert.management.commands.recomputestats import garbage_collect_topics
from courses.management.commands.load_crosswalk import get_crosswalk_s3
from courses.management.commands.merge_topics import prompt_for_link, similar_courses
from courses.models import Course, Topic
from PennCourses.settings.base import XWALK_SEMESTER_TO
from collections.abc import Iterable


def course_code_heuristics(full_codes: Iterable[str]) -> list[str]:
    """
    Produces a superset of the originally passed in full_codes by
    appending a 0 to the end of all 3 digit codes, and a 0 to the start
    of 3 digit codes that already start witha 0. e.g.
    if full_codes = ["MATH-014"], then the result is ["CIS-120"], ["CIS-1200", ""]
    """
    out = list(full_codes)
    for full_code in full_codes:
        dept, number = full_code.split("-")
        if len(number) == 4:
            # reverse the string and replace the first 0 possible; then reverse again
            out.append(f"{dept}-{number[::-1].replace('0', 1)[::-1]}")
    return out

def reform_topics(topic_ids=None, interactive=True, use_heuristics=True):
    # delete the topics
    # TODO: does `courses`` still contain the same courses once
    # we delete the topics associated with `topic_ids`?
    courses = Course.objects.all()
    if topic_ids is not None:
        courses = courses.filter(topic_id__in=topic_ids)
        courses = Course.objects.filter(id__in=list(courses.values_list("id", flat=True)))
    courses.update(topic=None)
    primary_listings = courses.filter(primary_listing_id=F("id"))
    garbage_collect_topics()

    # create topics for each primary listing
    for primary_listing in primary_listings:
        topic = Topic.objects.create(most_recent=primary_listing)
        primary_listing.listing_set.all().update(topic=topic)

    # compute mapping from new codes to old codes
    crosswalk = get_crosswalk_s3(verbose=True)
    rev_crosswalk = {}
    for old_code, new_codes in crosswalk.items():
        for new_code in new_codes:
            assert new_code not in rev_crosswalk
            rev_crosswalk[new_code] = old_code

    for semester in primary_listings.values_list("semester", flat=True).order_by("semester"):
        # pass 1: use crosswalk
        if semester == XWALK_SEMESTER_TO:
            for primary_listing in primary_listings.filter(full_code__in=rev_crosswalk.keys(), semester=semester):                        
                old_code = rev_crosswalk[primary_listing.full_code]
                prev_course = courses.filter(
                    full_code=old_code, semester__lt=semester
                ).order_by("-semester").first()
                
                # check if the old_code is already part of a different topic
                if (
                    not prev_course 
                    or prev_course.topic.most_recent.semester >= primary_listing.semester
                ):
                    # Assume we branched from this topic
                    primary_listing.topic.update(branched_from=prev_course.topic)
                    continue

                # if, possible merge the current course with the topic of old_code
                prev_course.topic.merge_with(primary_listing.topic)
            
        # pass 2: try to use course code
        for primary_listing in primary_listings.filter(semester=semester):
            if use_heuristics:
                full_codes = course_code_heuristics(primary_listing.listing_set.all().values_list("full_code", flat=True))
            else:
               full_codes = primary_listing.listing_set.all().values("full_code") 

            prev_courses = (
                courses
                .filter(
                    semester__lt=semester,
                    topic__most_recent__semester__lt=primary_listing.semester
                )
                .filter(full_code__in=full_codes)
                .annotate(
                    lineage_length=Count("topic__courses__semester") # TODO: is this only counting distinct semesters?
                )
                .order_by("-semester", "-lineage_length")
            )

            for i, prev_course in enumerate(prev_courses):
                # verify that the options are relatively close in title
                if not similar_courses(prev_course, primary_listing): # TODO: implement
                    print(
                        f"{str(prev_course)} is not very similar to {str(primary_listing)}. "
                        f"Have {len(prev_courses) - 1 - i} remaining options to link to."
                    )
                    if interactive and prompt_for_link(prev_course, primary_listing):
                        prev_course.topic.merge_with(primary_listing.topic)   
                else:
                    prev_course.topic.merge_with(primary_listing.topic) 


    garbage_collect_topics()

    pprint(list(courses.values_list("topic__id", "topic__most_recent", "topic__most_recent__semester").distinct()))
    
    # TODO: we should print where the overlap is
    overlaps = courses.filter(
        Exists(
            courses.exclude(
                topic_id=OuterRef("topic_id"),
            ).filter(
                full_code=OuterRef("full_code")
            )
        )
    ).values("full_code", "topic_id", "semester").order_by("full_code")
    if overlaps.exists():
        print("Found the same course code among multiple created topics:\n\n")
        pprint(list(overlaps))
        if interactive and input("abort? [y/N]") == "y":
            raise RuntimeError("Multiple topics for same course code")
    raise RuntimeError("Stop commit") # TODO: remove

class Command(BaseCommand):
    help = (
        "This script splits provided topics into their individual courses "
        "and then uses the cross walk and exact course code matches to re-form "
        "the courses into topics."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-t",
            "--topic-ids",
            nargs="*",
            help=dedent(
                """
            Specify a (space-separated) list of Topic IDs to split and merge.
            You can find Topic IDs from the django admin interface (either by searching through
            Topics or by following the topic field from a course entry). If none are provided
            then all topics are used.
            """
            ),
            required=False,
        )
        
        parser.add_argument(
            "-n",
            "--not-interactive",
            action="store_true",
            help="Make the command non-interactive"
        )
        
        parser.add_argument(
            "-e",
            "--no-heuristics",
            action="store_true",
            help=dedent(
                """
            Make the script disallow heuristics to match course codes (e.g., 
            translating between 4 and 3 digit course codes by removing 0s).
            """
            ),
        )

        

    def handle(self, *args, **kwargs):
        topic_ids = set(kwargs["topic_ids"]) if kwargs["topic_ids"] else None
        use_heuristics = not kwargs["no_heuristics"]
        interactive = not kwargs["not_interactive"]

        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        with transaction.atomic():
            reform_topics(
                topic_ids=topic_ids, 
                use_heuristics=use_heuristics, 
                interactive=interactive
            )

                                