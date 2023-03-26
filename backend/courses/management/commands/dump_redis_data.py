import json
import time

import redis
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from redis.commands.json.path import Path
from redis.commands.search.field import NumericField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from courses.models import Course, Topic
from review.annotations import annotate_average_and_recent
from review.util import get_average_and_recent_dict_single


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
        Topic.objects.filter(most_recent__semester="2023C")
        .select_related("most_recent")
        .prefetch_related("most_recent__primary_listing__listing_set__sections__instructors")
    )
    for topic in topics:
        course = topic.most_recent
        crosslistings = ", ".join([c.full_code for c in course.crosslistings])
        instructors = ", ".join(
            {instructor.name for s in course.sections.all() for instructor in s.instructors.all()}
        )
        course_qs = Course.objects.filter(pk=course.pk)
        course_qs = annotate_average_and_recent(
            course_qs,
            match_review_on=Q(section__course__topic=topic) & review_filters_pcr,
            match_section_on=Q(course__topic=topic) & section_filters_pcr,
            extra_metrics=True,
        )
        reviewed_course = (
            get_average_and_recent_dict_single(dict(course_qs.values()[0])) if course_qs else None
        )
        avg_reviews = reviewed_course["average_reviews"]
        yield {
            "code": course.full_code.replace("-", " "),
            "title": course.title,
            "crosslistings": crosslistings,
            "instructors": instructors,
            "description": course.description,
            "semester": course.semester,
            "course_quality": avg_reviews["rCourseQuality"]
            if "rCourseQuality" in avg_reviews
            else None,
            "difficulty": avg_reviews["rDifficulty"] if "rDifficulty" in avg_reviews else None,
            "work_required": avg_reviews["rWorkRequired"]
            if "rWorkRequired" in avg_reviews
            else None,
        }


def initialize_schema():
    r = redis.Redis().from_url(settings.REDIS_URL)
    schema = (
        TextField("$.code", as_name="code", weight=2, no_stem=True),
        TextField("$.crosslistings", as_name="crosslistings", weight=2, no_stem=True),
        TextField("$.instructors", as_name="instructors", no_stem=True, phonetic_matcher="dm:en"),
        TextField("$.title", as_name="title", weight=2),
        TextField("$.description", as_name="description"),
        TextField("$.semester", as_name="semester", no_stem=True),
        NumericField("$.course_quality", as_name="course_quality", sortable=True),
        NumericField("$.work_required", as_name="work_required", sortable=True),
        NumericField("$.difficulty", as_name="difficulty", sortable=True),
    )
    try:
        # Check if exists, will throw error if not
        r.ft("courses").info()
    except Exception:
        # If not, then create
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
