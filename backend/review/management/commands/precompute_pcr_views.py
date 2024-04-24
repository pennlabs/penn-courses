import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.http import Http404
from tqdm import tqdm

from courses.models import Topic
from review.models import CachedReviewResponse
from review.views import manual_course_reviews
from django.db import transaction

def precompute_pcr_views(verbose=False, is_new_data=False):
    if verbose:
        print("Now precomputing PCR reviews.")

    CachedReviewResponse.objects.all().update(expired=True)
    responses = CachedReviewResponse.objects.all()
    topic_set = {response.topic_id: response for response in responses}

    missing_objects = []
    objs_to_insert = []
    objs_to_update = []
    cache_deletes = set()
    has_count = total_count = 0

    # Iterate through all topics.
    with transaction.atomic():
        for topic in tqdm(
            Topic.objects.all().select_related("most_recent").order_by("most_recent__semester"),
            disable=not verbose,
        ):
            course_id_list, course_code_list = zip(*topic.courses.values_list("id", "full_code"))
            topic_id = ".".join([str(id) for id in sorted(course_id_list)])
            total_count += 1

            if topic_id in topic_set:
                try:
                    has_count += 1
                    response_obj = topic_set[topic_id]
                    if is_new_data:
                        response_obj.response = manual_course_reviews(
                            topic.most_recent.full_code, topic.most_recent.semester
                        )
                        cache_deletes.add(topic_id)
                    response_obj.expired = False
                    objs_to_update.append(response_obj)
                except Http404:
                    missing_objects.append((topic_id, topic.most_recent.full_code))
                    logging.info(
                        f"Topic returned 404 (topic_id {topic_id}, "
                        f"course_code {course_code_list[0]}, semester {topic.most_recent.semester})"
                    )
            else:
                try:
                    review_json = manual_course_reviews(topic.most_recent.full_code, topic.most_recent.semester)
                    objs_to_insert.append(
                        CachedReviewResponse(
                            topic_id=topic_id, response=review_json, expired=False
                        )
                    )
                    for course_code in course_code_list:
                        curr_topic_id = cache.get(course_code)
                        if curr_topic_id:
                            cache_deletes.add(curr_topic_id)
                        cache_deletes.add(course_code)
                except Http404:
                    missing_objects.append((topic_id, topic.most_recent.full_code))
                    logging.info(
                        f"Topic returned 404 (topic_id {topic_id}, "
                        f"course_code {course_code_list[0]}, semester {topic.most_recent.semester})"
                    )

        if verbose:
            print(f"{total_count} course reviews covered, {has_count} of which were already in the database. {len(objs_to_insert)} course reviews were created. {len(objs_to_update)} course reviews were updated.")

        # Bulk create / update objects.
        if verbose:
            print("Creating and updating objects.")
        CachedReviewResponse.objects.bulk_create(objs_to_insert)
        CachedReviewResponse.objects.bulk_update(objs_to_update, ["response", "expired"])

        # Bulk delete objects.
        if verbose:
            print("Deleting expired objects.")
        CachedReviewResponse.objects.filter(expired=True).delete()
        cache.delete_many(cache_deletes)

        print(missing_objects)

class Command(BaseCommand):
    help = "Precompute PCR views for all topics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--new_data", action="store_false", help="Include this flag to recalculate review data."
        )

    def handle(self, *args, **kwargs):
        precompute_pcr_views(verbose=True, is_new_data=kwargs["new_data"])
