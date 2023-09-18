from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, F, OuterRef

from alert.management.commands.recomputestats import garbage_collect_topics
from courses.management.commands.load_crosswalk import get_crosswalk_s3
from courses.models import Course, Topic


def form_simple_topics():
    Course.objects.all().update(topic=None)
    garbage_collect_topics()

    print("Cleared topics.")

    # create topics for each primary listing
    primary_listings = Course.objects.filter(primary_listing_id=F("id"))
    for primary_listing in primary_listings:
        topic = Topic.objects.create(most_recent=primary_listing)
        primary_listing.listing_set.all().update(topic=topic)

    print("Created new topics (one per course).")

    # merge topics based on full_code of primary_listing
    for full_code in primary_listings.values_list("full_code", flat=True):
        Topic.merge_all(
            list(
                set(
                    course.topic
                    for course in primary_listings.filter(full_code=full_code).select_related("topic")
                )
            )
        )

    print("Merged topics based on full_code")

    # use crosswalk
    crosswalk = get_crosswalk_s3(verbose=True)
    for old_code, new_codes in crosswalk.items():
        old_topic = Topic.objects.filter(most_recent__listing_set__full_code=old_code).first()
        new_course = (
            Course.objects.filter(
                full_code__in=new_codes,
            )
            .annotate(
                title_matches=Exists(  # Prefer Course.objects.all().with matching title
                    Course.objects.all().filter(full_code=old_code, title=OuterRef("title"))
                ),
            )
            .order_by("-title_matches")
            .select_related("topic")
            .first()
        )
        if old_topic and new_course:
            new_course.topic.merge_with(old_topic)

    print("Merged topics based on crosswalk")

    garbage_collect_topics()

    print("Done!")


class Command(BaseCommand):
    help = (
        "This script deletes all existing topics and re-creates them "
        "so that courses with the same full_code are in the same topic. "
        "this script also uses the crosswalk. "
    )

    def handle(self, *args, **kwargs):
        print(
            "This script is atomic, meaning either all Topic changes will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        with transaction.atomic():
            form_simple_topics()
