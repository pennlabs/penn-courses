import logging

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Topic
from PennCourses.settings.base import CACHE_PREFIX
from review.models import CachedReviewResponse
from review.views import manual_course_reviews


def precompute_pcr_views(verbose=False, is_new_data=False):
    if verbose:
        print("Now precomputing PCR reviews.")

    objs_to_insert = []
    objs_to_update = []
    cache_deletes = set()
    valid_reviews_in_db = total_reviews = 0

    with transaction.atomic():
        # Mark all the topics as expired.
        CachedReviewResponse.objects.all().update(expired=True)
        cached_responses = CachedReviewResponse.objects.all()
        topic_id_to_response_obj = {response.topic_id: response for response in cached_responses}

        # Iterate through all topics.
        for topic in tqdm(
            Topic.objects.all().select_related("most_recent").order_by("most_recent__semester"),
            disable=not verbose,
        ):
            # get topic id
            course_id_list, course_code_list = zip(*topic.courses.values_list("id", "full_code"))
            topic_id = ".".join([str(id) for id in sorted(course_id_list)])
            total_reviews += 1

            if topic_id in topic_id_to_response_obj:
                # current topic id is already cached
                valid_reviews_in_db += 1
                response_obj = topic_id_to_response_obj[topic_id]
                response_obj.expired = False

                if is_new_data:
                    cache_deletes.add(CACHE_PREFIX + topic_id)
                    review_data = manual_course_reviews(
                        topic.most_recent.full_code, topic.most_recent.semester
                    )
                    if not review_data:
                        logging.info(
                            f"Invalid review data for ("
                            f"topic_id={topic_id},"
                            f"course_code={course_code_list[0]},"
                            f"semester={topic.most_recent.semester})"
                        )
                        continue
                    response_obj.response = review_data
                objs_to_update.append(response_obj)
            else:
                # current topic id is not cached
                review_data = manual_course_reviews(
                    topic.most_recent.full_code, topic.most_recent.semester
                )
                if not review_data:
                    logging.info(
                        f"Invalid review data for ("
                        f"topic_id={topic_id},"
                        f"course_code={course_code_list[0]},"
                        f"semester={topic.most_recent.semester})"
                    )
                    continue

                objs_to_insert.append(
                    CachedReviewResponse(topic_id=topic_id, response=review_data, expired=False)
                )
                for course_code in course_code_list:
                    curr_topic_id = cache.get(CACHE_PREFIX + course_code)
                    if curr_topic_id:
                        cache_deletes.add(CACHE_PREFIX + curr_topic_id)
                    cache_deletes.add(CACHE_PREFIX + course_code)

        if verbose:
            print(
                f"{total_reviews} course reviews covered, "
                f"{valid_reviews_in_db} of which were already in the database. "
                f"{len(objs_to_insert)} course reviews were created. "
                f"{len(objs_to_update)} course reviews were updated."
            )

        # Bulk create / update objects.
        if verbose:
            print("Creating and updating objects.")
        CachedReviewResponse.objects.bulk_create(objs_to_insert, batch_size=4000)
        CachedReviewResponse.objects.bulk_update(
            objs_to_update, ["response", "expired"], batch_size=4000
        )

        # Bulk delete objects.
        if verbose:
            print("Deleting expired objects.")
        CachedReviewResponse.objects.filter(expired=True).delete()
        cache.delete_many(cache_deletes)


class Command(BaseCommand):
    help = "Precompute PCR views for all topics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--new_data",
            action="store_true",
            help="Include this flag to recalculate review data.",
        )

    def handle(self, *args, **kwargs):
        precompute_pcr_views(verbose=True, is_new_data=kwargs["new_data"])
