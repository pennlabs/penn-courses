from textwrap import dedent

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from backend.alert.management.commands.recomputestats import garbage_collect_topics
from backend.courses.management.commands.load_crosswalk import get_crosswalk_s3
from backend.courses.util import decr_semester
from courses.models import Course, Topic
from PennCourses.settings.base import XWALK_SEMESTER_TO


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
            Topics or by following the topic field from a course entry).
            """
            ),
            required=True,
        )

    def handle(self, *args, **kwargs):
        topic_ids = set(kwargs["topic_ids"])

        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        with transaction.atomic():
            # delete the topics
            # TODO: does `courses`` still contain the same courses once
            # we delete the topics associated with `topic_ids`?
            courses = Course.objects.filter(topic_id__in=topic_ids)
            courses.update(topic=None)
            primary_listings = courses.filter(primary_listings=F("id"))
            garbage_collect_topics()

            # create topics for each primary listing
            for primary_listing in primary_listings:
                topic = Topic.objects.create(most_recent=primary_listing)
                primary_listing.listing_set.all().update(topic=topic)

            # first load from the crosswalk
            crosswalk = get_crosswalk_s3(verbose=True)
            rev_crosswalk = {}
            for old_code, new_codes in crosswalk.items():
                for new_code in new_codes:
                    rev_crosswalk[new_code] = (
                        old_code,
                        new_codes.length > 1,
                    )  # the old code and whether the old_code branches

            for primary_listing in primary_listings.order_by("semester"):
                # look for a course from the previous semester that shares a
                # full code with the primary_listing or one of its crosslistings
                prev_sem = decr_semester(primary_listing.semester)
                if not courses.filter(semester=prev_sem).exists():
                    continue

                # Use the crosswalk
                if (
                    primary_listing.semester == XWALK_SEMESTER_TO
                    and primary_listing.full_code in rev_crosswalk
                ):
                    # try to get the previous course
                    old_code, is_branched = rev_crosswalk[primary_listing.full_code]

                    # NOTE: this ignores `old_code` if the matching course
                    # is not in `courses`. This may not be intended behavior since
                    # it ignores what is in the crosswalk sometimes.
                    if (
                        prev_course := courses.objects.filter(full_code=old_code, semester=prev_sem)
                        .first()
                        .primary_listing
                    ):
                        if is_branched:
                            primary_listing.topic.branched_from = prev_course.topic
                            primary_listing.topic.save()
                        else:
                            primary_listing.topic.merge_with(prev_course.topic)

                # preferentially look for an exactly matching primary_listing
                # from the previous semester
                try:
                    primary_listings.filter(
                        semester=prev_sem,
                        full_code=primary_listing.full_code,
                        topic__most_recent__semester=prev_sem,
                    ).get().topic.merge_with(topic)
                    continue
                except ObjectDoesNotExist:
                    pass

                # otherwise, try to find a course from the previous semester
                # with the same code as in the listing set
                if prev_course := courses.filter(
                    semester=prev_sem,
                    full_code=primary_listing.full_code,
                    # make sure this topic doesn't already have a course in the same semester
                    topic__most_recent__semester=prev_sem,
                ).first():
                    prev_course.topic.merge_with(topic)
