import json
import time

import redis
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, Q, Subquery
from redis.commands.json.path import Path
from redis.commands.search.field import NumericField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

from courses.models import Course, Topic, Department, Instructor, Section
from review.annotations import annotate_average_and_recent
from review.util import get_average_and_recent_dict_single
from review.views import course_filters_pcr, section_filters_pcr, review_filters_pcr

def get_department_objs():
    departments = Department.objects.all()
    for department in departments:
        yield {
            "code": department.code,
            "name": department.name
        }

def get_course_objs():
    topics = (
        Topic.objects.filter(most_recent__semester="2022C")
        .select_related("most_recent")
        .prefetch_related("most_recent__primary_listing__listing_set__sections__instructors")
    )
    for topic in topics:
        course = topic.most_recent
        crosslistings = ", ".join([c.full_code for c in course.crosslistings])
        instructors = ", ".join({instructor.name for s in course.sections.all() for instructor in s.instructors.all()})
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

def join_depts(depts):
    try:
        return ",".join(sorted(list(depts)))
    except TypeError:
        return ""

def get_instructor_objs():
    instructors = (
        Instructor.objects.filter(
            id__in=Subquery(Section.objects.filter(section_filters_pcr).values("instructors__id"))
        )
        .distinct()[:100]
        .values("name", "id", "section__course__department__code")
    )
    instructor_set = {}
    for inst in instructors:
        if inst["id"] not in instructor_set:
            instructor_set[inst["id"]] = {
                "title": inst["name"],
                "desc": set([inst["section__course__department__code"]]),
                "id": inst["id"],
            }
        instructor_set[inst["id"]]["desc"].add(inst["section__course__department__code"])
    
    for instructor in instructor_set.values():
        yield {
            "name": instructor["title"],
            "desc": join_depts(instructor["desc"]),
            "id": str(instructor["id"])
        }

def initialize_schema():
    r = redis.Redis().from_url(settings.REDIS_URL)

    # Department Schema
    department_schema = (
        TextField("$.code", as_name="code", weight=1, no_stem=True),
        TextField("$.name", as_name="name", weight=1, no_stem=True)
    )

    # Course Schema
    course_schema = (
        TextField("$.code", as_name="code", weight=20, no_stem=True),
        TextField("$.crosslistings", as_name="crosslistings", weight=3, no_stem=True),
        TextField("$.instructors", as_name="instructors", weight=2, no_stem=True, phonetic_matcher="dm:en"),
        TextField("$.title", as_name="title", weight=4),
        TextField("$.description", as_name="description", weight=2),
        TextField("$.semester", as_name="semester", no_stem=True, weight=0),
        NumericField("$.course_quality", as_name="course_quality", sortable=True),
        NumericField("$.work_required", as_name="work_required", sortable=True),
        NumericField("$.difficulty", as_name="difficulty", sortable=True),
    )

    # Instructor Schema
    instructor_schema = (
        TextField("$.id", as_name="id", weight=0),
        TextField("$.name", as_name="name", weight=4, no_stem=True, phonetic_matcher="dm:en"),
        TextField("$.desc", as_name="desc", weight=1, no_stem=True)
    )

    # check if schema exists, else create schema
    try:
        r.ft("departments").info()
    except Exception:
        r.ft("departments").create_index(
            department_schema, definition=IndexDefinition(prefix=["department:"], index_type=IndexType.JSON)
        )
    try:
        r.ft("courses").info()
    except Exception:
        r.ft("courses").create_index(
            course_schema, definition=IndexDefinition(prefix=["course:"], index_type=IndexType.JSON)
        )
    try:
        r.ft("instructors").info()
    except Exception:
        r.ft("instructors").create_index(
            instructor_schema, definition=IndexDefinition(prefix=["instructor:"], index_type=IndexType.JSON)
        )


def dump_data(department_data, course_data, instructor_data):
    r = redis.Redis().from_url(settings.REDIS_URL)
    p = r.pipeline()

    # department data
    for department in department_data:
        p.json().set(name=f"department:{department['code']}", path=Path.root_path(), obj=department)

    # course data
    for course in course_data:
        p.json().set(name=f"course:{course['code']}", path=Path.root_path(), obj=course)

    # instructor data
    for instructor in instructor_data:
        p.json().set(name=f"instructor:{instructor['id']}", path=Path.root_path(), obj=instructor)
    
    print(
        "Error while loading metadata into Redis"
        if False in p.execute()
        else "Successfully loaded metadata into Redis"
    )

def reset_database():
    r = redis.Redis().from_url(settings.REDIS_URL)
    r.flushdb()

def dump_autocomplete_data_to_redis(verbose=True):
    if verbose:
        print("\n=== Dumping data into Redis ===")
    reset_database()
    if verbose:
        print("Cleared Redis database...")
    initialize_schema()
    if verbose:
        print("  Initialized Redis schema...")
    department_data = get_department_objs()
    if verbose:
        print("  Fetch departments...")
    course_data = get_course_objs()
    if verbose:
        print("  Fetch courses...")
    instructor_data = get_instructor_objs()
    if verbose:
        print("  Fetch instructors...")
    dump_data(
        department_data,
        course_data,
        instructor_data
    )
    if verbose:
        print("=== Done ===")


class Command(BaseCommand):
    help = """Load in the courses' metadata into Redis for full-text searching"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print out verbose information",
        )

    def handle(self, *args, **kwargs):
        verbose = kwargs["verbose"]
        dump_autocomplete_data_to_redis(verbose=verbose)