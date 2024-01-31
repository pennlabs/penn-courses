
from django.core.management.base import BaseCommand
from tqdm import tqdm

from review.views import manual_course_reviews 
from courses.util import get_current_semester
from courses.models import Topic
from django.core.cache import caches

PCR_PRECOMPUTED_CACHE_PREFIX = "pcr_precomputed_"

def precompute_pcr_views():
    current_semester = get_current_semester()
    blue_cache = caches["blue"]
    green_cache = caches["green"]
    green_cache.clear()

    for topic in tqdm(Topic.objects.all()):
        course_id_list, course_code_list = zip(*topic.courses.values_list("id", "full_code"))
        topic_id = ".".join([str(id) for id in sorted(course_id_list)])
        if blue_cache.get(topic_id) is None:
            green_cache.set(
                PCR_PRECOMPUTED_CACHE_PREFIX + topic_id,
                manual_course_reviews(course_code_list[0], None),
            )  # placeholder semester
        else:
            green_cache.set(PCR_PRECOMPUTED_CACHE_PREFIX + topic_id, blue_cache.get(topic_id))

        for course_code in course_code_list:
            green_cache.set(course_code, topic_id)

    caches["blue"], caches["green"] = green_cache, blue_cache


class Command(BaseCommand):
    help = "Precompute PCR views for all topics"

    def handle(self, *args, **kwargs):
        precompute_pcr_views()
