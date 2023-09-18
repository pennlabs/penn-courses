from pprint import pprint
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Exists, OuterRef, Count, Q

from alert.management.commands.recomputestats import garbage_collect_topics
from backend.courses.util import get_current_semester
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

def reform_topics(min_semester=None, interactive=True, use_heuristics=True):
    # delete the topics
    # TODO: does `courses` still contain the same courses once
    # we delete the topics associated with `topic_ids`?
    courses = Course.objects.all()
    Course.objects.all().update(topic=None)
    primary_listings = Course.objects.all().filter(primary_listing_id=F("id"))
    garbage_collect_topics()

    # create topics for each primary listing
    for primary_listing in primary_listings:
        topic = Topic.objects.create(most_recent=primary_listing)
        primary_listing.listing_set.all().update(topic=topic)

    semester_filter = Q()
    if min_semester is None:
        semester_filter = Q(semester=get_current_semester())
    elif min_semester == "all":
        pass
    else:
        semester_filter = Q(semester__gte=min_semester)

    # compute mapping from new codes to old codes
    crosswalk = get_crosswalk_s3(verbose=True)

    for semester in (
        primary_listings
        .filter(semester_filter)
        .values_list("semester", flat=True)
        .order_by("semester")
        .distinct()
    ):
        # pass 1: use crosswalk
        if semester == XWALK_SEMESTER_TO:
            for old_code, new_codes in crosswalk.items():                     
                prev_course = Course.objects.all().filter(
                    full_code=old_code, semester__lt=semester
                ).order_by("-semester").first()
                if not prev_course:
                    continue

                # TODO: this is logically inconsistent with the assumption that we
                # are progressing semester by semester, since these new_codes could 
                # be for many semesters in the future. Breaking this assumption
                # means that we could end up having partially filled topics.
                for new_code in new_codes:
                    next_code = Course.objects.all().filter(
                        full_code=new_code, semester__gt=semester
                    ).order_by("semester").first()
                    if not next_code:
                        continue
                    next_code.set_previously(prev_course)
                
        # pass 2: try to use course code
        for primary_listing in primary_listings.filter(semester=semester):
            if use_heuristics:
                full_codes = course_code_heuristics(
                    primary_listing.listing_set.all().values_list("full_code", flat=True)
                )
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
                    if not interactive or not prompt_for_link(prev_course, primary_listing):
                        continue  
                primary_listing.set_previously(prev_course) 


    garbage_collect_topics()

    pprint(list(Course.objects.all().values_list("topic__id", "topic__most_recent", "topic__most_recent__semester").distinct()))
    
    # TODO: we should print where the overlap is
    overlaps = Course.objects.all().filter(
        Exists(
            Course.objects.all().exclude(
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
            "-s",
            "--min-semester",
            type=str,
            help=dedent(
                """
                The semester to start the script at, or "all" to start from the earliest 
                semester. If this argument is omitted, the script will use the current 
                semester (as determined by `get_current_semester()`).
                """
            ),
            nargs="?",
            default=None,
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
        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        use_heuristics = not kwargs["no_heuristics"]
        interactive = not kwargs["not_interactive"]
        with transaction.atomic():
            reform_topics(
                min_semester=kwargs["min_semester"],
                use_heuristics=use_heuristics, 
                interactive=interactive
            )

                                