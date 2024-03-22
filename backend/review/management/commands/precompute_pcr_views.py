
from django.core.management.base import BaseCommand
from tqdm import tqdm

from review.views import manual_course_reviews 
from courses.models import Topic
from review.models import CachedReviewResponse
from django.core.cache import caches
from django.conf import settings
from django.http import Http404
import logging
import redis

def precompute_pcr_views(verbose=False, is_new_data=False):
    if verbose:
        print("Now precomputing PCR reviews.")
    
    # Mark all reviews in the table as expired.
    responses = CachedReviewResponse.objects.all()
    for response in responses:
        response.expired = True
    responses.bulk_update()
    topic_set = {response.topic_id: response for response in responses}

    objs_to_insert = []
    objs_to_update = []
    
    for topic in tqdm(
        Topic.objects
        .all()
        .select_related("most_recent")
        .order_by("most_recent__semester"),
        disable=not verbose
    ):
        course_id_list, course_code_list = zip(*topic.courses.values_list("id", "full_code"))
        topic_id = ".".join([str(id) for id in sorted(course_id_list)])

        if topic_id in topic_set:
            response_obj = topic_set[topic_id]
            if is_new_data:
                response_obj.response=manual_course_reviews(course_code_list[0], topic.most_recent.semester)
            response_obj.expired = False
            objs_to_update.append(response_obj)
        else:
            try:
                objs_to_insert.append(
                    CachedReviewResponse.objects.create(
                        topic_id=topic_id,
                        response=manual_course_reviews(course_code_list[0], topic.most_recent.semester),
                        expired=False
                    )
                )
            except Http404:
                logging.info(f"Topic returned 404 (topic_id {topic_id}, "
                    f"course_code {course_code_list[0]}, semester {topic.most_recent.semester})")

    # Clean out all expired reviews.
    CachedReviewResponse.objects.filter(expired=True).delete()
    CachedReviewResponse.objects.bulk_create(objs_to_insert)
    CachedReviewResponse.objects.bulk_update(objs_to_update, ["response", "expired"])


def redis_precompute_pcr_views(verbose=False):
    blue_cache = caches["blue"]
    green_cache = caches["green"]
    green_cache.clear()

    # Note: we only cache the most recent topic for each full_code (any other cache entries get overwritten)
    for topic in tqdm(
        Topic.objects
        .all()
        .select_related("most_recent")
        .order_by("most_recent__semester"),
        disable=not verbose
    ):
        course_id_list, course_code_list = zip(*topic.courses.values_list("id", "full_code"))
        topic_id = ".".join([str(id) for id in sorted(course_id_list)])
        if blue_cache.get(topic_id) is None:
            try:
                green_cache.set(
                    topic_id,
                    manual_course_reviews(course_code_list[0], topic.most_recent.semester),
                )
            except Http404:
                logging.info(f"Topic returned 404 (topic_id {topic_id}, "
                             f"course_code {course_code_list[0]}, semester {topic.most_recent.semester})")
        else:
            green_cache.set(topic_id, blue_cache.get(topic_id))

        for course_code in course_code_list:
            green_cache.set(course_code, topic_id)

    blue_redis_url, blue_redis_db = settings.CACHES.get("blue").get("LOCATION").rsplit("/", 1)
    green_redis_url, green_redis_db = settings.CACHES.get("green").get("LOCATION").rsplit("/", 1)
    assert blue_redis_url == green_redis_url, "Expect blue and green to use the same redis instance! Aborting blue green swap."
    r = redis.Redis.from_url(blue_redis_url)

    # swap blue and green
    r.swapdb(int(blue_redis_db), int(green_redis_db))

class Command(BaseCommand):
    help = "Precompute PCR views for all topics"

    def handle(self, *args, **kwargs):
        precompute_pcr_views(verbose=True)
