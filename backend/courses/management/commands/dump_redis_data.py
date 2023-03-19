from courses.models import Course, Topic
from django.core.management.base import BaseCommand
from review.management.commands.clearcache import clear_cache
from django.conf import settings
from django.db.models import Q, F
from review.util import get_single_dict_from_qs, get_average_and_recent_dict_single
from review.annotations import annotate_average_and_recent
import json
import redis


course_filters_pcr_allow_xlist = ~Q(title="") | ~Q(description="") | Q(sections__has_reviews=True)
course_filters_pcr = Q(primary_listing_id=F("id")) & course_filters_pcr_allow_xlist
course_filters_pcr_allow_xlist = ~Q(title="") | ~Q(description="") | Q(sections__has_reviews=True)

section_filters_pcr = Q(course__primary_listing_id=F("course_id")) & (
    Q(has_reviews=True)
    | ((~Q(course__title="") | ~Q(course__description="")) & ~Q(activity="REC") & ~Q(status="X"))
)

review_filters_pcr = Q(section__course__primary_listing_id=F("section__course_id"))


def get_course_objs():
    topics = (
        Topic.objects.all()
        .select_related("most_recent")
        .prefetch_related("primary_listing__listing_set")
    )
    for topic in topics:
        course = topic.most_recent
        crosslistings = course.crosslistings
        course_qs = annotate_average_and_recent(
            course,
            match_review_on=Q(section__course__topic=topic) & review_filters_pcr,
            match_section_on=Q(course__topic=topic) & section_filters_pcr,
            extra_metrics=True,
        )
        reviewed_course = dict(course_qs[0].values()) if course_qs else None
        reviewed_course = get_average_and_recent_dict_single(reviewed_course)
        yield json.dumps(
            {
                "code": course["full_code"].replace("-", " "),
                "title": course["title"],
                "crosslistings": crosslistings,
                "description": course["description"],
                "semester": course["semester"],
                "course_quality": reviewed_course["average_reviews"]["rCourseQuality"]
                if reviewed_course
                else None,
                "difficulty": reviewed_course["average_reviews"]["rDifficulty"]
                if reviewed_course
                else None,
                "work_required": reviewed_course["average_reviews"]["rWorkRequired"]
                if reviewed_course
                else None,
            }
        )


class Command(BaseCommand):

    help = """Load in the courses' metadata into Redis for full-text searching"""

    def handle(self, *args, **kwargs):

        # Initialise schema (TODO: rm03)

        URL = settings.REDIS_URL
        r = redis.Redis.from_url(URL)

        # Write to Redis (TODO: rm03)

        for course in get_course_objs():
            pass
