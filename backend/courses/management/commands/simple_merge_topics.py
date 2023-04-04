import json
from django.db.models import Subquery, OuterRef, Exists
from courses.models import Course, Topic
from django.db import transaction
from django.contrib.postgres.fields import ArrayField
from django.core.management.base import BaseCommand
from django.db.models import TextField
from django.conf import settings
from django.db.models import Q, F
from tqdm import tqdm


def get_stat():
    d = {}

    def stat(name):
        if d.get(name) is None:
            d[name] = 0
            return
        d[name] += 1
    return d, stat


class ArraySubquery(Subquery):
    template = 'ARRAY(%(subquery)s)'
    output_field = ArrayField(base_field=TextField())


def group_and_merge_on_subquery(array_subquery, set_stat, verbose=False):
    overlapping_topics_set = Course.objects \
        .select_related("topic", "topic__courses") \
        .annotate(overlapping_topics=array_subquery) \
        .filter(overlapping_topics__len__gt=0) \
        .values_list("topic", "overlapping_topics")\
        .distinct()

    merge_count = 0
    with transaction.atomic():
        merged_topics = set()
        for (topic, overlapping_topics) in tqdm(overlapping_topics_set):
            # Note: overlapping_topics and merged_topics may contain invalid ids as we merge and delete topics
            overlapping_topics = set(overlapping_topics)
            overlapping_topics.add(topic)
            if overlapping_topics <= merged_topics:  # we've already merged these
                set_stat("already_merged")
                continue

            # get all the primary listings
            courses = Course.objects\
            .filter(primary_listing=F("id"))\
            .filter(
                Q(topic__id__in=overlapping_topics) | Q(topic__id=topic)
            ).distinct()  # NOTE: distinct with value is postgresonly!
            semesters = courses.values_list("semester", flat=True)

            # there are some overlapping semesters, don't merge
            if len(semesters) != len(set(semesters)):
                set_stat("overlapping_semesters")
                continue

            # get input on merge
            if verbose and input(f"merge {courses.values_list('full_code', 'semester')}").lower().strip() != "y":
                continue

            mergeable_topics = Topic.objects.filter(id__in=overlapping_topics)

            # topics should not be merged if they have different `branched_from`s
            branched_from = mergeable_topics\
                .exclude(branched_from__isnull=True)\
                .values_list("branched_from", flat=True)\
                .distinct()
            if len(branched_from) > 1:
                set_stat("different_branched_from")
                continue

            Topic.merge_all(mergeable_topics)
            merged_topics |= overlapping_topics
            merge_count += 1

    return merge_count

def simple_merge(verbose=False):
    """
    Quickly identifies and merges groups of topics:
    1) containing crosslistings
    2) that share the same `most_recent__full_code`
    obeying topic invariants along the way.
    """

    if 'django.db.backends.postgresql' not in settings.DATABASES['default']['ENGINE']:
        print("This script can only be used with postgres backend!")
        return

    overlapping_stats, set_overlapping_stats = get_stat()
    overlapping_topics_subquery = ArraySubquery(  # filters down to around 1/2
        Course.objects
        .exclude(topic=OuterRef("topic"))
        .filter(primary_listing=OuterRef("primary_listing"))
        .values_list("topic")
    )
    overlapping_merges = group_and_merge_on_subquery(
        overlapping_topics_subquery,
        set_overlapping_stats,
        verbose=verbose
    )
    print(f"overlapping topic merges: {overlapping_merges}")
    print("stats:")
    print(json.dumps(overlapping_stats, default=str, indent=2))

    sequential_stats, set_sequential_stats = get_stat()
    sequential_topics_subquery = ArraySubquery(
        # This subquery identifies courses where...
        Course.objects # ...other courses have:
        .select_related("topic__most_recent", "primary_listing")
        .exclude(topic=OuterRef("topic"))  # ... a different topic ...
        .filter(
            semester__lt=OuterRef("semester"),  # ... an earlier semester
            full_code=OuterRef("full_code")
        )
        .values_list("topic", flat=True)
        .distinct()
    )
    sequential_merges = group_and_merge_on_subquery(
        sequential_topics_subquery,
        set_sequential_stats,
        verbose=verbose
    )
    print(f"sequential topic merges: {sequential_merges}")
    print("stats:")
    print(json.dumps(sequential_stats, default=str, indent=2))


class Command(BaseCommand):
    help = (
        "This script merges topics with crosslisted courses (while preserving topic invariants)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
        )

    def handle(self, *args, **kwargs):
        simple_merge(verbose=kwargs["verbose"])