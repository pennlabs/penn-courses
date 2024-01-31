import logging

import redis
from django.conf import settings
from django.core.cache import caches
from django.core.management import BaseCommand

def clear_cache(clear_pcr_cache=False, _cache_alias="default", _redis_delete_keys="*views.decorators.cache*"):
    # If we are not using redis as the cache backend, then we can delete everything from the cache.
    if (
        settings.CACHES is None
        or settings.CACHES.get(_cache_alias).get("BACKEND") != "django_redis.cache.RedisCache"
    ):
        caches[_cache_alias].clear()
        return -1

    # If redis is the cache backend, then we need to be careful to only delete django cache entries,
    # since celery also uses redis as a message broker backend.
    r = redis.Redis.from_url(settings.REDIS_URL)
    del_count = 0
    for key in r.scan_iter(_redis_delete_keys):
        r.delete(key)
        del_count += 1

    if clear_pcr_cache:
        # avoid circular import
        from courses.management.commands.precompute_pcr_views import PCR_PRECOMPUTED_CACHE_PREFIX
        del_count += clear_cache(clear_pcr_cache=False, _cache_alias="green", _redis_delete_keys=f"{PCR_PRECOMPUTED_CACHE_PREFIX}*")
        del_count += clear_cache(clear_pcr_cache=False, _cache_alias="blue", _redis_delete_keys=f"{PCR_PRECOMPUTED_CACHE_PREFIX}*")

    return del_count


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--clear_pcr_cache",
            action="store_true",
            help="If set, will clear the PCR cache as well.",
        )

    def handle(self, *args, **options):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        del_count = clear_cache(clear_pcr_cache=options["clear_pcr_cache"])
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
