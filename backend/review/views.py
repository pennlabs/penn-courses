from collections import Counter, defaultdict

from dateutil.tz import gettz
from django.core.cache import cache
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv
from openai import OpenAI
import os
import re
import json
import time
import uuid
import redis
from django.db import connection
import numpy as np

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

from courses.models import (
    Course,
    Department,
    Instructor,
    NGSSRestriction,
    PreNGSSRestriction,
    Section,
)
from courses.util import get_current_semester, get_or_create_add_drop_period, prettify_semester
from PennCourses.docs_settings import PcxAutoSchema
from PennCourses.settings.base import CACHE_PREFIX, TIME_ZONE, WAITLIST_DEPARTMENT_CODES, REDIS_URL
from review.annotations import annotate_average_and_recent, review_averages
from review.documentation import (
    ACTIVITY_CHOICES,
    autocomplete_response_schema,
    course_plots_response_schema,
    course_reviews_response_schema,
    department_reviews_response_schema,
    instructor_for_course_reviews_response_schema,
    instructor_reviews_response_schema,
)
from review.models import ALL_FIELD_SLUGS, CachedReviewResponse, Review
from review.util import (
    aggregate_reviews,
    avg_and_recent_demand_plots,
    avg_and_recent_percent_open_plots,
    get_average_and_recent_dict_single,
    get_num_sections,
    get_single_dict_from_qs,
    get_status_updates_map,
    make_subdict,
)
r = redis.Redis.from_url(REDIS_URL)

"""
You might be wondering why these API routes are using the @api_view function decorator
from Django REST Framework rather than using any of the higher-level constructs that DRF
gives us, like Generic APIViews or ViewSets.

ViewSets define REST actions on a specific "resource" -- generally in our case, django models with
defined serializers. With these aggregations, though, there isn't a good way to define a resource
for a ViewSet to act upon. Each endpoint doesn't represent one resource, or a list of resources,
but one aggregation of all resources (ReviewBits) that fit a certain filter.

There probably is a way to fit everything into a serializer, but at the time of writing it felt like
it'd be shoe-horned in so much that it made more sense to use "bare" ApiViews.
"""


# A Q filter defining which sections we will include in demand distribution estimates,
# also used by extra_metrics_section_filters_pcr (see below)
extra_metrics_section_filters = (
    ~Q(
        course__department__code__in=WAITLIST_DEPARTMENT_CODES
    )  # Manually filter out classes from depts with waitlist systems during add/drop
    & Q(capacity__gt=0)
    & ~Q(course__semester__icontains="b")  # Filter out summer classes
    & Q(has_status_updates=True)
    & ~Q(
        id__in=Subquery(
            NGSSRestriction.special_approval().values("sections__id"))
    )  # Filter out sections that require permit for registration
    & ~Q(
        id__in=Subquery(
            PreNGSSRestriction.special_approval().values("sections__id"))
    )  # Filter out sections that require permit for registration (pre-NGSS)
)


def extra_metrics_section_filters_pcr(current_semester=None):
    """
    This function returns a Q filter for sections that should be included in
    extra PCR plots / metrics.
    """
    if current_semester is None:
        current_semester = get_current_semester()
    return extra_metrics_section_filters & Q(course__semester__lt=current_semester) & ~Q(status="X")


course_filters_pcr = ~Q(title="") | ~Q(
    description="") | Q(sections__has_reviews=True)
section_filters_pcr = Q(has_reviews=True) | (
    (~Q(course__title="") | ~Q(course__description="")) & ~Q(
        activity="REC") & ~Q(status="X")
)

HOUR_IN_SECONDS = 60 * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24
MONTH_IN_SECONDS = DAY_IN_SECONDS * 30


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_path_parameter_desc={
            "course-reviews": {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    )
                }
            },
        },
        custom_parameters={
            "course-reviews": {
                "GET": [
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                ]
            },
        },
        override_response_schema=course_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def course_reviews(request, course_code, semester=None):
    request_semester = request.GET.get("semester")

    topic_id = cache.get(CACHE_PREFIX + course_code)
    if topic_id is None:
        try:
            recent_course = most_recent_course_from_code(
                course_code, request_semester)
        except Course.DoesNotExist:
            raise Http404()
        topic = recent_course.topic
        course_id_list = list(topic.courses.values_list("id"))
        topic_id = ".".join([str(id[0]) for id in sorted(course_id_list)])
        cache.set(CACHE_PREFIX + course_code, topic_id, MONTH_IN_SECONDS)

    response = cache.get(CACHE_PREFIX + topic_id)
    if response is None:
        cached_response = CachedReviewResponse.objects.filter(
            topic_id=topic_id).first()
        if cached_response is None:
            response = manual_course_reviews(course_code, request_semester)
            if not response:
                raise Http404()
        else:
            response = cached_response.response
        cache.set(CACHE_PREFIX + topic_id, response, MONTH_IN_SECONDS)

    return Response(response)


def most_recent_course_from_code(course_code, semester):
    return (
        Course.objects.filter(
            course_filters_pcr,
            **(
                {
                    "topic__courses__full_code": course_code,
                    "topic__courses__semester": semester,
                }
                if semester
                else {"full_code": course_code}
            ),
        )
        .order_by("-semester")[:1]
        .annotate(
            branched_from_full_code=F(
                "topic__branched_from__most_recent__full_code"),
            branched_from_semester=F(
                "topic__branched_from__most_recent__semester"),
        )
        .select_related("topic__most_recent")
        .get()
    )


def manual_course_reviews(course_code, request_semester):
    """
    Get all reviews for the topic of a given course and other relevant information.
    Different aggregation views are provided, such as reviews spanning all semesters,
    only the most recent semester, and instructor-specific views.
    """
    semester = request_semester
    try:
        course = most_recent_course_from_code(course_code, request_semester)
    except Course.DoesNotExist:
        return None

    topic = course.topic
    branched_from_full_code = course.branched_from_full_code
    branched_from_semester = course.branched_from_semester
    course = topic.most_recent
    course_code = course.full_code
    aliases = list(course.crosslistings.values_list("full_code", flat=True))

    superseded = False
    if semester:
        max_semester = (
            Course.objects.filter(
                course_filters_pcr,
                full_code=course_code,
            )
            .aggregate(max_semester=Max("semester"))
            .get("max_semester")
        )
        if max_semester:
            superseded = max_semester > course.semester
    last_offered_sem_if_superceded = course.semester if superseded else None

    topic_codes = list(
        topic.courses.exclude(full_code=course.full_code)
        .values("full_code")
        .annotate(semester=Max("semester"), branched_from=Value(False))
        .values("full_code", "semester", "branched_from")
    )
    topic_branched_from = (
        {
            "full_code": branched_from_full_code,
            "semester": branched_from_semester,
            "branched_from": True,
        }
        if branched_from_full_code
        else None
    )
    historical_codes = sorted(
        topic_codes + ([topic_branched_from] if topic_branched_from else []),
        key=lambda x: x["semester"],
        reverse=True,
    )

    instructor_reviews = review_averages(
        Review.objects.filter(section__course__topic=topic),
        reviewbit_subfilters=Q(review_id=OuterRef("id")),
        section_subfilters=Q(id=OuterRef("section_id")),
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    ).annotate(instructor_name=F("instructor__name"), semester=F("section__course__semester"))
    recent_instructors = list(
        Instructor.objects.filter(
            id__in=Subquery(
                Section.objects.filter(section_filters_pcr, course__topic=topic).values(
                    "instructors__id"
                )
            )
        )
        .distinct()
        .annotate(
            most_recent_sem=Subquery(
                Section.objects.filter(
                    instructors__id=OuterRef("id"), course__topic=topic)
                .annotate(common=Value(1))
                .values("common")
                .annotate(max_sem=Max("course__semester"))
                .values("max_sem")
            )
        )
        .values(
            instructor_id=F("id"),
            instructor_name=F("name"),
            semester=F("most_recent_sem"),
        )
    )
    for instructor in recent_instructors:
        instructor["exclude_from_recent"] = True
    all_instructors = list(instructor_reviews.values()) + recent_instructors
    instructors = aggregate_reviews(
        all_instructors, "instructor_id", name="instructor_name")

    course_qs = annotate_average_and_recent(
        Course.objects.filter(course_filters_pcr,
                              topic_id=topic.id).order_by("-semester")[:1],
        match_review_on=Q(section__course__topic=topic),
        match_section_on=Q(course__topic=topic) & section_filters_pcr,
        extra_metrics=True,
    )
    course = get_single_dict_from_qs(course_qs)

    num_registration_metrics = Section.objects.filter(
        extra_metrics_section_filters_pcr(),
        course__topic=topic,
    ).count()

    num_sections, num_sections_recent = get_num_sections(
        section_filters_pcr,
        course__topic=topic,
    )

    return {
        "code": course["full_code"],
        "last_offered_sem_if_superceded": last_offered_sem_if_superceded,
        "name": course["title"],
        "description": course["description"],
        "aliases": aliases,
        "historical_codes": historical_codes,
        "latest_semester": course["semester"],
        "num_sections": num_sections,
        "num_sections_recent": num_sections_recent,
        "instructors": instructors,
        "registration_metrics": num_registration_metrics > 0,
        **get_average_and_recent_dict_single(course),
    }


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-plots": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Plots retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_parameters={
            "course-plots": {
                "GET": [
                    {
                        "name": "course_code",
                        "in": "path",
                        "description": "The dash-joined department and code of the course you want plots for, e.g. `CIS-120` for CIS-120.",  # noqa: E501
                        "schema": {"type": "string"},
                        "required": True,
                    },
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                    {
                        "name": "instructor_ids",
                        "in": "query",
                        "description": "A comma-separated list of instructor IDs with which to filter the sections underlying the returned plots."  # noqa: E501
                        "Note that if only invalid instructor IDs are present, plot response fields will be null or 0.",  # noqa: E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                ]
            },
        },
        override_response_schema=course_plots_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def course_plots(request, course_code):
    """
    Get all PCR plots for a given course.
    """
    try:
        semester = request.query_params.get("semester")
        course = (
            Course.objects.filter(
                course_filters_pcr,
                **(
                    {
                        "topic__courses__full_code": course_code,
                        "topic__courses__semester": semester,
                    }
                    if semester
                    else {"full_code": course_code}
                ),
            )
            .order_by("-semester")[:1]
            .select_related("topic__most_recent")
            .get()
        ).topic.most_recent
    except Course.DoesNotExist:
        raise Http404()

    current_semester = get_current_semester()

    # Compute set of sections to include in plot data
    filtered_sections = (
        Section.objects.filter(
            extra_metrics_section_filters_pcr(current_semester),
            course__topic_id=course.topic_id,
        )
        .annotate(efficient_semester=F("course__semester"))
        .distinct()
    )
    instructor_ids = request.GET.get("instructor_ids")
    if instructor_ids:
        instructor_ids = [int(id) for id in instructor_ids.split(",")]
        filtered_sections = filtered_sections.filter(
            instructors__id__in=instructor_ids,
        ).distinct()

    # a dict mapping semester to section id to section object
    section_map = defaultdict(dict)
    for section in filtered_sections:
        section_map[section.efficient_semester][section.id] = section

    (
        avg_demand_plot,
        avg_demand_plot_min_semester,
        recent_demand_plot,
        recent_demand_plot_semester,
        avg_percent_open_plot,
        avg_percent_open_plot_min_semester,
        recent_percent_open_plot,
        recent_percent_open_plot_semester,
    ) = tuple([None] * 8)
    avg_demand_plot_num_semesters, avg_percent_open_plot_num_semesters = (0, 0)
    if section_map:
        status_updates_map = get_status_updates_map(section_map)
        (
            avg_demand_plot,
            avg_demand_plot_min_semester,
            avg_demand_plot_num_semesters,
            recent_demand_plot,
            recent_demand_plot_semester,
        ) = avg_and_recent_demand_plots(section_map, status_updates_map, bin_size=0.005)
        (
            avg_percent_open_plot,
            avg_percent_open_plot_min_semester,
            avg_percent_open_plot_num_semesters,
            recent_percent_open_plot,
            recent_percent_open_plot_semester,
        ) = avg_and_recent_percent_open_plots(section_map, status_updates_map)

    current_adp = get_or_create_add_drop_period(current_semester)
    local_tz = gettz(TIME_ZONE)

    return Response(
        {
            "code": course_code,
            "current_add_drop_period": {
                "start": current_adp.estimated_start.astimezone(tz=local_tz),
                "end": current_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": {
                "pca_demand_plot_since_semester": avg_demand_plot_min_semester,
                "pca_demand_plot_num_semesters": avg_demand_plot_num_semesters,
                "pca_demand_plot": avg_demand_plot,
                "percent_open_plot_since_semester": avg_percent_open_plot_min_semester,
                "percent_open_plot_num_semesters": avg_percent_open_plot_num_semesters,
                "percent_open_plot": avg_percent_open_plot,
            },
            "recent_plots": {
                "pca_demand_plot_since_semester": recent_demand_plot_semester,
                "pca_demand_plot_num_semesters": (1 if recent_demand_plot is not None else 0),
                "pca_demand_plot": recent_demand_plot,
                "percent_open_plot_since_semester": recent_percent_open_plot_semester,
                "percent_open_plot_num_semesters": (1 if recent_demand_plot is not None else 0),
                "percent_open_plot": recent_percent_open_plot,
            },
        }
    )


def check_instructor_id(instructor_id):
    if not isinstance(instructor_id, int) and not (
        isinstance(instructor_id, str) and instructor_id.isdigit()
    ):
        raise Http404("Instructor with given instructor_id not found.")


INSTRUCTOR_COURSE_REVIEW_FIELDS = [
    "instructor_quality",
    "course_quality",
    "work_required",
    "difficulty",
]


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "instructor-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Instructor with given instructor_id not found.",
                },
            },
        },
        custom_path_parameter_desc={
            "instructor-reviews": {
                "GET": {
                    "instructor_id": (
                        "The integer id of the instructor you want reviews for. Note that you can get the relative path for any instructor including this id by using the `url` field of objects in the `instructors` list returned by Retrieve Autocomplete Data."  # noqa E501
                    )
                }
            },
        },
        override_response_schema=instructor_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def instructor_reviews(request, instructor_id):
    """
    Get all reviews for a given instructor, aggregated by course.
    """
    check_instructor_id(instructor_id)
    instructor = get_object_or_404(Instructor, id=instructor_id)
    instructor_qs = annotate_average_and_recent(
        Instructor.objects.filter(id=instructor_id),
        match_review_on=Q(instructor_id=instructor_id),
        match_section_on=Q(
            instructors__id=instructor_id) & section_filters_pcr,
        extra_metrics=True,
    )
    inst = get_single_dict_from_qs(instructor_qs)

    courses = annotate_average_and_recent(
        Course.objects.filter(
            course_filters_pcr,
            sections__instructors__id=instructor_id,
        ).distinct(),
        match_review_on=Q(
            section__course__topic=OuterRef(OuterRef("topic")),
            instructor_id=instructor_id,
        ),
        match_section_on=Q(
            course__topic=OuterRef(OuterRef("topic")),
            instructors__id=instructor_id,
        ),
        extra_metrics=True,
        fields=INSTRUCTOR_COURSE_REVIEW_FIELDS,
    ).annotate(
        most_recent_full_code=F("topic__most_recent__full_code"),
    )

    num_sections, num_sections_recent = get_num_sections(
        section_filters_pcr,
        course_id__in=Subquery(
            Course.objects.filter(
                course_filters_pcr,
                sections__instructors__id=instructor_id,
            ).values("id")
        ),
    )

    # Return the most recent course taught by this instructor, for each topic
    courses_res = dict()
    max_sem = dict()
    for r in courses.values():
        if not r["average_semester_count"]:
            continue
        full_code = r["most_recent_full_code"]
        if full_code not in max_sem or max_sem[full_code] < r["semester"]:
            max_sem[full_code] = r["semester"]
            courses_res[full_code] = get_average_and_recent_dict_single(
                r,
                full_code="most_recent_full_code",
                code="most_recent_full_code",
                name="title",
            )

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": num_sections_recent,
            "num_sections": num_sections,
            "courses": courses_res,
            **get_average_and_recent_dict_single(inst),
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "department-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Department with the given department_code not found.",
                }
            }
        },
        custom_path_parameter_desc={
            "department-reviews": {
                "GET": {
                    "department_code": (
                        "The department code you want reviews for, e.g. `CIS` for the CIS department."  # noqa E501
                    )
                }
            },
        },
        override_response_schema=department_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def department_reviews(request, department_code):
    """
    Get reviews for all courses in a department.
    """
    department = get_object_or_404(Department, code=department_code)

    topic_id_to_course = dict()
    recent_courses = list(
        Course.objects.filter(
            course_filters_pcr,
            department=department,
        )
        .distinct()
        .values("semester", "topic_id", course_title=F("title"), course_code=F("full_code"))
    )
    for c in recent_courses:
        c["exclude_from_recent"] = True
        topic_id = c["topic_id"]
        if (
            topic_id not in topic_id_to_course
            or topic_id_to_course[topic_id]["semester"] < c["semester"]
        ):
            topic_id_to_course[topic_id] = c

    reviews = list(
        review_averages(
            Review.objects.filter(section__course__department=department),
            reviewbit_subfilters=Q(review_id=OuterRef("id")),
            section_subfilters=Q(id=OuterRef("section_id")),
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
        )
        .annotate(
            topic_id=F("section__course__topic_id"),
            semester=F("section__course__semester"),
        )
        .values()
    )
    for review in reviews:
        course = topic_id_to_course[review["topic_id"]]
        review["course_code"] = course["course_code"]
        review["course_title"] = course["course_title"]

    all_courses = reviews + list(topic_id_to_course.values())
    courses = aggregate_reviews(
        all_courses, "course_code", code="course_code", name="course_title")

    return Response({"code": department.code, "name": department.name, "courses": courses})


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-history": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Invalid course_code or instructor_id.",
                }
            }
        },
        custom_path_parameter_desc={
            "course-history": {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    ),
                    "instructor_id": ("The integer id of the instructor you want reviews for."),
                }
            },
        },
        custom_parameters={
            "course-history": {
                "GET": [
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    }
                ]
            },
        },
        override_response_schema=instructor_for_course_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def instructor_for_course_reviews(request, course_code, instructor_id):
    """
    Get the review history of an instructor teaching a course.
    """
    try:
        semester = request.GET.get("semester")
        course = (
            Course.objects.filter(
                course_filters_pcr,
                **(
                    {
                        "topic__courses__full_code": course_code,
                        "topic__courses__semester": semester,
                    }
                    if semester
                    else {"full_code": course_code}
                ),
            )
            .order_by("-semester")[:1]
            .select_related("topic__most_recent")
            .get()
        )
        course = course.topic.most_recent
    except Course.DoesNotExist:
        raise Http404()

    check_instructor_id(instructor_id)
    instructor = get_object_or_404(Instructor, id=instructor_id)

    reviews = review_averages(
        Review.objects.filter(
            section__course__topic_id=course.topic_id, instructor_id=instructor_id
        ),
        reviewbit_subfilters=Q(review_id=OuterRef("id")),
        section_subfilters=Q(id=OuterRef("section_id")),
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    )
    reviews = list(
        reviews.annotate(
            course_code=F("section__course__full_code"),
            course_title=F("section__course__title"),
            activity=F("section__activity"),
            efficient_semester=F("section__course__semester"),
        ).values()
    )
    existing_sections = {r["section_id"] for r in reviews}
    all_sections = reviews + [
        s
        for s in Section.objects.filter(
            section_filters_pcr,
            course__topic_id=course.topic_id,
            instructors__id=instructor_id,
        )
        .distinct()
        .values(
            "id",
            "activity",
            course_code=F("course__full_code"),
            course_title=F("course__title"),
            efficient_semester=F("course__semester"),
        )
        if s["id"] not in existing_sections
    ]
    all_sections.sort(key=lambda s: s["efficient_semester"], reverse=True)

    return Response(
        {
            "instructor": {
                "id": instructor_id,
                "name": instructor.name,
            },
            "course_code": course.full_code,
            "sections": [
                {
                    "course_code": section["course_code"],
                    "course_name": section["course_title"],
                    "activity": ACTIVITY_CHOICES.get(section["activity"]),
                    "semester": section["efficient_semester"],
                    "forms_returned": section.get("responses"),
                    "forms_produced": section.get("enrollment"),
                    "ratings": make_subdict("bit_", section),
                    "comments": section.get("comments"),
                }
                for section in all_sections
            ],
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "review-autocomplete": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Autocomplete dump retrieved successfully."},
            },
        },
        override_response_schema=autocomplete_response_schema,
    )
)
def autocomplete(request):
    """
    Autocomplete entries for Courses, departments, instructors. All objects have title, description,
    and url. This route does not have any path parameters or query parameters, it just dumps
    all the information necessary for frontend-based autocomplete. It is also cached
    to improve performance.
    """

    courses = (
        Course.objects.filter(course_filters_pcr)
        .annotate(
            max_semester=Subquery(
                Course.objects.filter(full_code=OuterRef(
                    "full_code"), topic=OuterRef("topic"))
                .annotate(common=Value(1))
                .values("common")
                .annotate(max_semester=Max("semester"))
                .values("max_semester")
            )
        )
        .filter(semester=F("max_semester"))
        .values("full_code", "title", "topic_id", "max_semester")
        .distinct("full_code", "topic_id")
    )
    code_counter = Counter(c["full_code"] for c in courses)

    def get_prefix(course: Course) -> str:
        return (
            f"({prettify_semester(course['max_semester'])}) "
            if code_counter[course["full_code"]] > 1
            else ""
        )

    semester_prefix = get_prefix

    course_set = sorted(
        [
            {
                "title": semester_prefix(course) + course["full_code"],
                "desc": [course["title"]],
                "url": f"/course/{course['full_code']}/{course['max_semester']}",
            }
            for course in courses
        ],
        key=lambda x: x["title"],
    )
    departments = Department.objects.all().values("code", "name")
    department_set = sorted(
        [
            {
                "title": dept["code"],
                "desc": dept["name"],
                "url": f"/department/{dept['code']}",
            }
            for dept in departments
        ],
        key=lambda d: d["title"],
    )

    instructors = (
        Instructor.objects.filter(
            id__in=Subquery(Section.objects.filter(
                section_filters_pcr).values("instructors__id"))
        )
        .distinct()
        .values("name", "id", "section__course__department__code")
    )
    instructor_set = {}
    for inst in instructors:
        if inst["id"] not in instructor_set:
            instructor_set[inst["id"]] = {
                "title": inst["name"],
                "desc": set([inst["section__course__department__code"]]),
                "url": f"/instructor/{inst['id']}",
            }
        instructor_set[inst["id"]]["desc"].add(
            inst["section__course__department__code"])

    def join_depts(depts):
        try:
            return ",".join(sorted(list(depts)))
        except TypeError:
            return ""

    instructor_set = sorted(
        [
            {
                "title": v["title"],
                "desc": join_depts(v["desc"]),
                "url": v["url"],
            }
            for v in instructor_set.values()
        ],
        key=lambda x: x["title"],
    )

    return Response(
        {
            "courses": course_set,
            "departments": department_set,
            "instructors": instructor_set,
        }
    )


CHAT_TTL_SECONDS = 7 * 24 * 3600
MAX_MESSAGES_PER_CHAT = 50
MAX_CHATS_PER_DAY = 5


def _today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def _new_chat_id():
    return uuid.uuid4().hex[:8]


def _make_msg(role, content, citations=None):
    return json.dumps({
        "id": uuid.uuid4().hex,
        "role": role,
        "content": content,
        "citations": citations or [],
        "ts": int(time.time()),
    })

# key naming helpers
#api that we can call to and check if it works 
#call build llm with retreived rag courses
def _quota_key(user_id, date, what):
    return f"quota:{user_id}:{date}:{what}"


def _chat_meta_key(chat_id):
    return f"chat:{chat_id}:meta"


def _chat_messages_key(chat_id):
    return f"chat:{chat_id}:messages"


def check_and_incr_quota(key, limit, ttl):
    used_raw = r.get(key)
    used = int(used_raw) if used_raw is not None else 0
    if used >= limit:
        return False
    
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl)
    pipe.execute()
    return True


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_start(request):
    user_id = request.user.id
    today = _today()

    if not check_and_incr_quota(
            _quota_key(user_id, today, "chats"),
            MAX_CHATS_PER_DAY,
            24 * 60 * 60):
        return Response({"error": "Daily quota exceeded"}, status=429)

    chat_id = _new_chat_id()
    meta = {"user_id": user_id, "created_at": int(time.time())}
    r.set(_chat_meta_key(chat_id), json.dumps(meta), ex=CHAT_TTL_SECONDS)
    r.delete(_chat_messages_key(chat_id))
    r.expire(_chat_messages_key(chat_id), CHAT_TTL_SECONDS)

    return Response({
        "chat_id": chat_id,
        "expires_at": int(time.time()) + CHAT_TTL_SECONDS,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat_message(request, chat_id):
    user_id = request.user.id
    text = request.data.get("text")
    if not text:
        return Response({"error": "Missing 'text'"}, status=400)

    meta = r.get(_chat_meta_key(chat_id))
    if not meta:
        return Response({"error": "Chat not found or expired"}, status=404)

    mquota = f"quota:{chat_id}:messages"
    used_raw = r.get(mquota)
    used = int(used_raw) if used_raw is not None else 0
    if used >= MAX_MESSAGES_PER_CHAT:
        return Response({"error": "Message quota exceeded"}, status=429)

    pipe = r.pipeline()
    pipe.incr(mquota)
    pipe.expire(mquota, CHAT_TTL_SECONDS)
    pipe.execute()

    umsg = _make_msg("user", text)
    r.rpush(_chat_messages_key(chat_id), umsg)

    # Get chat history
    history_msgs_raw = r.lrange(_chat_messages_key(chat_id), 0, -1) or []
    history_msgs = [json.loads(m) for m in history_msgs_raw]
    
    # RAG: Retrieve courses → Build prompt → Call LLM (all in one function)
    reply_text, citations = call_llm(text, history_msgs=history_msgs, top_k=10)
    
    amsg = _make_msg("assistant", reply_text, citations=citations)
    r.rpush(_chat_messages_key(chat_id), amsg)
    r.expire(_chat_messages_key(chat_id), CHAT_TTL_SECONDS)

    return Response(json.loads(amsg))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def chat_history(request, chat_id):
    limit = int(request.GET.get("limit", 20))
    msgs = r.lrange(_chat_messages_key(chat_id), -limit, -1) or []
    parsed = [json.loads(m) for m in msgs]
    return Response({"messages": parsed})


SYSTEM_PROMPT = """You are the Penn Course Review assistant.
Answer questions using the provided 'Context' about courses.

If the user asks about courses in general (e.g., "CS courses", "computer science courses"), 
provide information about the courses mentioned in the Context, even if it's just a few examples.

If specific information is completely missing from Context, respond: 
"I'm not sure. Try using Penn Course Review search."

Always:
- Include course codes (e.g., CIS-120, CIS 1200)
- Cite every factual claim using citations like (1), (2)
- Be concise: short bullet points or a short paragraph
- If asked about course types/categories, describe the courses in Context as examples
- Avoid quoting long student reviews
- Never invent courses, stats, prerequisites, or opinions
"""

def build_prompt(history_msgs, retrieved_docs, user_query, max_history_turns=3):
    """
    history_msgs: list[dict] - messages stored in Redis (user + assistant)
    retrieved_docs: list[dict] - docs returned by RAG
    user_query: str
    """
    
    prompt_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]

    context = []
    for i, doc in enumerate(retrieved_docs, start=1):
        code = doc.get("course_code", "UNKNOWN")
        text = doc.get("text", "")
        url = doc.get("url", "")
        context.append(f"({i}) {code}: {text} [cite]({url})")

    if context:
        context_block = "Context:\n" + "\n".join(context)
        prompt_msgs.append({"role": "system", "content": context_block})
    
    if history_msgs:
        trimmed = history_msgs[-(max_history_turns * 2):]
        for msg in trimmed:
            prompt_msgs.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    prompt_msgs.append({"role": "user", "content": user_query})
    return prompt_msgs

def _extract_citations(text: str):
    return re.findall(r"\[cite\]\((/course/[^)]+)\)", text)


def retrieve_courses(user_query: str, top_k: int = 10):
    """
    RAG: Retrieve relevant courses from pgvector database based on user query.
    Searches ALL 27,106 embedded courses using semantic similarity.
    
    Args:
        user_query: The user's query text
        top_k: Number of top courses to retrieve (default: 10)
    
    Returns:
        List of dicts with course_code, text, url, and similarity score
    """
    if not user_query:
        return []
    
    try:
        # Embed the user query
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=user_query
        )
        query_embedding = response.data[0].embedding
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Search ALL courses in pgvector using cosine similarity
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    course_code,
                    text,
                    url,
                    1 - (embedding <=> %s::vector) as similarity
                FROM course_documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, [embedding_str, embedding_str, top_k])
            
            results = cursor.fetchall()
            
            retrieved_docs = []
            for row in results:
                course_code, text, url, similarity = row
                retrieved_docs.append({
                    "course_code": course_code or "UNKNOWN",
                    "text": text or "",
                    "url": url or "",
                    "similarity": float(similarity) if similarity else 0.0
                })
            
            return retrieved_docs
    except Exception as e:
        print(f"Error retrieving courses: {e}")
        return []


def call_llm(user_query: str, history_msgs: list = None, top_k: int = 10):
    """
    Complete RAG pipeline: Retrieve courses → Build prompt → Query LLM.
    
    Args:
        user_query: The user's query text
        history_msgs: Optional chat history (list of message dicts)
        top_k: Number of courses to retrieve for context (default: 10)
    
    Returns:
        Tuple of (response_text, citations)
    """
    if not user_query:
        return "Please provide a query.", []
    
    # Step 1: Retrieve relevant courses using RAG
    retrieved_docs = retrieve_courses(user_query, top_k=top_k)
    
    # Step 2: Build prompt with retrieved context
    prompt_messages = build_prompt(history_msgs or [], retrieved_docs, user_query)
    
    # Step 3: Call LLM with the prompt
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        output_text = response.choices[0].message.content
        citations = _extract_citations(output_text)
        return output_text, citations
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return "I'm sorry, I encountered an error. Please try again.", []