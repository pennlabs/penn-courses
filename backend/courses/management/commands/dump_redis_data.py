import redis
import json
from courses.models import Course, Topic
from django.conf import settings
from django.core.management.base import BaseCommand
from review.management.commands.clearcache import clear_cache
from django.conf import settings
from django.db.models import Q, F
from review.util import get_single_dict_from_qs, get_average_and_recent_dict_single
from review.annotations import annotate_average_and_recent
from redis.commands.json.path import Path
from redis.commands.search.field import TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType


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
    c = 0
    for topic in topics:
        if c > 100:
            break
        c += 1
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


def initialize_schema():
    r = redis.Redis().from_url(settings.REDIS_URL)
    schema = (
        TextField("$.code", as_name="code", weight=2, no_stem=True),
        TextField("$.crosslistings", as_name="crosslistings", weight=2, no_stem=True),
        TextField("$.title", as_name="title", weight=2),
        TextField("$.description", as_name="description"),
        TextField("$.semester", as_name="semester", no_stem=True),
        NumericField("$.course_quality", as_name="course_quality", sortable=True),
        NumericField("$.work_required", as_name="work_required", sortable=True),
        NumericField("$.difficulty", as_name="difficulty", sortable=True),
    )
    r.ft("courses").create_index(
        schema, definition=IndexDefinition(prefix=["course:"], index_type=IndexType.JSON)
    )


def dump_data(course_data):
    r = redis.Redis().from_url(settings.REDIS_URL)
    p = r.pipeline()
    for course in course_data:
        p.json().set(name=f"course:{course['code']}", path=Path.root_path(), obj=course)

    print(
        "Error while loading metadata into Redis"
        if False in p.execute()
        else "Successfully loaded metadata into Redis"
    )


class Command(BaseCommand):

    help = """Load in the courses' metadata into Redis for full-text searching"""

    def handle(self, *args, **kwargs):
        initialize_schema()
        course_data = get_course_objs()
        dump_data(course_data)
