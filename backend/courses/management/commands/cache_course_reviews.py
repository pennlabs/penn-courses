import django.utils.timezone as timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.models import Course, Section, course_reviews, sections_with_reviews


REVIEW_FIELDS = [
    "course_quality",
    "difficulty",
    "instructor_quality",
    "work_required",
]

PREFIX = "precompute_"

fields_to_update = [f"{PREFIX}{field}" for field in REVIEW_FIELDS] + ["annotation_expiration"]


def _cache_reviews(queryset, model, desc, verbose):
    to_update = []
    expiration = timezone.now() + timezone.timedelta(days=30)
    for obj in tqdm(queryset, desc=desc, disable=not verbose):
        for field in REVIEW_FIELDS:
            setattr(obj, f"{PREFIX}{field}", getattr(obj, field))
        obj.annotation_expiration = expiration
        to_update.append(obj)

    with transaction.atomic():
        model.objects.bulk_update(to_update, fields_to_update, batch_size=500)


def cache_course_reviews(verbose=False):
    if verbose:
        print("Calculating Course review averages...")
    _cache_reviews(course_reviews(Course.objects.all()), Course, "Updating Courses", verbose)
    if verbose:
        print("Calculating Section review averages...")
    _cache_reviews(
        sections_with_reviews(Section.objects.all()), Section, "Updating Sections", verbose
    )


class Command(BaseCommand):
    help = "Calculates and persists review averages for Course and Section."

    def handle(self, *args, **options):
        cache_course_reviews(verbose=True)
        self.stdout.write(self.style.SUCCESS("Finished caching review averages."))
