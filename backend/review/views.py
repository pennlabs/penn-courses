from collections import defaultdict

from dateutil.tz import gettz
from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import redis
import re

# def highlight(self, tags=None):
#     fields = ['code', 'crosslistings', 'instructors', 'title', 'description', 'semester', 'course_quality', 'work_required', 'difficulty']

#     # add return command
#     return_args = ["RETURN"] + len(fields) + fields
#     self._return_fields = return_args

#     # add highlight command
#     args += ["HIGHLIGHT", "fields"] + len(fields) + fields

#     if tags:
#     else:


#     self._highlight_fields = args
#     return self

# FT.SEARCH courses "French" RETURN 2 title description HIGHLIGHT fields 2 title description


import json
from django.conf import settings
from redis.commands.search.query import NumericFilter, Query


from courses.models import Course, Department, Instructor, PreNGSSRestriction, Section
from courses.util import get_current_semester, get_or_create_add_drop_period
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from PennCourses.settings.base import (
    PRE_NGSS_PERMIT_REQ_RESTRICTION_CODES,
    TIME_ZONE,
    WAITLIST_DEPARTMENT_CODES,
)
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
from review.models import ALL_FIELD_SLUGS, Review
from review.util import (
    aggregate_reviews,
    avg_and_recent_demand_plots,
    avg_and_recent_percent_open_plots,
    get_average_and_recent_dict_single,
    get_historical_codes,
    get_num_sections,
    get_single_dict_from_qs,
    get_status_updates_map,
    make_subdict,
)


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
            PreNGSSRestriction.objects.filter(
                code__in=PRE_NGSS_PERMIT_REQ_RESTRICTION_CODES
            ).values("sections__id")
        )
    )  # Filter out sections that require permit for registration
    # TODO: get permit information from new OpenData API
)


def extra_metrics_section_filters_pcr(current_semester=None):
    """
    This function returns a Q filter for sections that should be included in
    extra PCR plots / metrics.
    """
    if current_semester is None:
        current_semester = get_current_semester()
    return (
        extra_metrics_section_filters
        & Q(course__primary_listing_id=F("course_id"))
        & Q(course__semester__lt=current_semester)
        & ~Q(status="X")
    )


course_filters_pcr_allow_xlist = ~Q(title="") | ~Q(description="") | Q(sections__has_reviews=True)
course_filters_pcr = Q(primary_listing_id=F("id")) & course_filters_pcr_allow_xlist

section_filters_pcr = Q(course__primary_listing_id=F("course_id")) & (
    Q(has_reviews=True)
    | ((~Q(course__title="") | ~Q(course__description="")) & ~Q(activity="REC") & ~Q(status="X"))
)

review_filters_pcr = Q(section__course__primary_listing_id=F("section__course_id"))

reviewbit_filters_pcr = Q(
    review__section__course__primary_listing_id=F("review__section__course_id")
)


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("course-reviews", args=["course_code"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_path_parameter_desc={
            reverse_func("course-reviews", args=["course_code"]): {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    )
                }
            },
        },
        override_response_schema=course_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def course_reviews(request, course_code):
    """
    Get all reviews for the topic of a given course and other relevant information.
    Different aggregation views are provided, such as reviews spanning all semesters,
    only the most recent semester, and instructor-specific views.
    """
    try:
        course = (
            Course.objects.filter(course_filters_pcr_allow_xlist, full_code=course_code)
            .order_by("-semester")[:1]
            .select_related(
                "topic",
                "topic__most_recent",
                "topic__branched_from",
                "topic__branched_from__most_recent",
            )
            .prefetch_related("topic__courses")
            .get()
        )
    except Course.DoesNotExist:
        raise Http404()

    topic = course.topic
    course = topic.most_recent
    course_code = course.full_code
    aliases = course.crosslistings.values_list("full_code", flat=True)

    instructor_reviews = review_averages(
        Review.objects.filter(review_filters_pcr, section__course__topic=topic),
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
                Section.objects.filter(instructors__id=OuterRef("id"), course__topic=topic)
                .annotate(common=Value(1))
                .values("common")
                .annotate(max_sem=Max("course__semester"))
                .values("max_sem")
            )
        )
        .values(instructor_id=F("id"), instructor_name=F("name"), semester=F("most_recent_sem"))
    )
    for instructor in recent_instructors:
        instructor["exclude_from_recent"] = True
    all_instructors = list(instructor_reviews.values()) + recent_instructors
    instructors = aggregate_reviews(all_instructors, "instructor_id", name="instructor_name")

    course_qs = annotate_average_and_recent(
        Course.objects.filter(course_filters_pcr, topic=topic).order_by("-semester")[:1],
        match_review_on=Q(section__course__topic=topic) & review_filters_pcr,
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

    return Response(
        {
            "code": course["full_code"],
            "name": course["title"],
            "description": course["description"],
            "aliases": aliases,
            "historical_codes": get_historical_codes(
                topic, exclude_codes=set(aliases) | {course["full_code"]}
            ),
            "latest_semester": course["semester"],
            "num_sections": num_sections,
            "num_sections_recent": num_sections_recent,
            "instructors": instructors,
            "registration_metrics": num_registration_metrics > 0,
            **get_average_and_recent_dict_single(course),
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("course-plots", args=["course_code"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Plots retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_parameters={
            reverse_func("course-plots", args=["course_code"]): {
                "GET": [
                    {
                        "name": "course_code",
                        "in": "path",
                        "description": "The dash-joined department and code of the course you want plots for, e.g. `CIS-120` for CIS-120.",  # noqa: E501
                        "schema": {"type": "string"},
                        "required": True,
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
        course = (
            Course.objects.filter(course_filters_pcr, full_code=course_code)
            .order_by("-semester")[:1]
            .select_related("topic", "topic__most_recent")
            .get()
        )
    except Course.DoesNotExist:
        raise Http404()

    course = course.topic.most_recent

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

    section_map = defaultdict(dict)  # a dict mapping semester to section id to section object
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
                "pca_demand_plot_num_semesters": 1 if recent_demand_plot is not None else 0,
                "pca_demand_plot": recent_demand_plot,
                "percent_open_plot_since_semester": recent_percent_open_plot_semester,
                "percent_open_plot_num_semesters": 1 if recent_demand_plot is not None else 0,
                "percent_open_plot": recent_percent_open_plot,
            },
        }
    )


def check_instructor_id(instructor_id):
    if not isinstance(instructor_id, int) and not (
        isinstance(instructor_id, str) and instructor_id.isdigit()
    ):
        raise Http404("Instructor with given instructor_id not found.")


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("instructor-reviews", args=["instructor_id"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Instructor with given instructor_id not found.",
                },
            },
        },
        custom_path_parameter_desc={
            reverse_func("instructor-reviews", args=["instructor_id"]): {
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
        match_review_on=Q(instructor_id=instructor_id) & review_filters_pcr,
        match_section_on=Q(instructors__id=instructor_id) & section_filters_pcr,
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
        )
        & review_filters_pcr,
        match_section_on=Q(
            course__topic=OuterRef(OuterRef("topic")),
            instructors__id=instructor_id,
        )
        & section_filters_pcr,
        extra_metrics=True,
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
                r, full_code="most_recent_full_code", code="most_recent_full_code", name="title"
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
            reverse_func("department-reviews", args=["department_code"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Department with the given department_code not found.",
                }
            }
        },
        custom_path_parameter_desc={
            reverse_func("department-reviews", args=["department_code"]): {
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
            course_filters_pcr_allow_xlist,
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
    courses = aggregate_reviews(all_courses, "course_code", code="course_code", name="course_title")

    return Response({"code": department.code, "name": department.name, "courses": courses})


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("course-history", args=["course_code", "instructor_id"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Invalid course_code or instructor_id.",
                }
            }
        },
        custom_path_parameter_desc={
            reverse_func("course-history", args=["course_code", "instructor_id"]): {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    ),
                    "instructor_id": ("The integer id of the instructor you want reviews for."),
                }
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
        course = (
            Course.objects.filter(course_filters_pcr_allow_xlist, full_code=course_code)
            .order_by("-semester")[:1]
            .select_related("topic", "topic__most_recent")
            .get()
        )
    except Course.DoesNotExist:
        raise Http404()

    check_instructor_id(instructor_id)
    instructor = get_object_or_404(Instructor, id=instructor_id)

    topic = course.topic
    course = course.topic.most_recent

    reviews = review_averages(
        Review.objects.filter(
            review_filters_pcr, section__course__topic=topic, instructor_id=instructor_id
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
            course__topic=topic,
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
            reverse_func("review-autocomplete"): {
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
        Course.objects.filter(course_filters_pcr_allow_xlist)
        .order_by("semester")
        .values("full_code", "title")
        .distinct()
    )
    course_set = sorted(
        [
            {
                "title": course["full_code"],
                "desc": [course["title"]],
                "url": f"/course/{course['full_code']}",
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
            id__in=Subquery(Section.objects.filter(section_filters_pcr).values("instructors__id"))
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
        instructor_set[inst["id"]]["desc"].add(inst["section__course__department__code"])

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
        {"courses": course_set, "departments": department_set, "instructors": instructor_set}
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("review-quick-search"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Search successful."},
            },
        },
        # override_response_schema=autocomplete_response_schema,
    )
)
def quick_search(request):
    """
    Completes quick search.
    """
    r = redis.Redis.from_url(settings.REDIS_URL)
    text_query = request.query_params.get("q")
    text_query = re.sub(r"[^a-zA-Z0-9@]+", "", text_query)
    if text_query:
        text_query += "|" + text_query + "*"
    course_quality = request.query_params.get("course_quality")
    course_difficulty = request.query_params.get("course_difficulty")
    work_required = request.query_params.get("work_required")

    # filters
    search_term = Query(text_query) \
        .return_fields('code', 'crosslistings', 'instructors', 'title', 'description', 'semester', 'course_quality', 'work_required', 'difficulty') \
        .highlight(tags=["<span style='background-color: yellow;'>", "</span>"]) \
        .scorer("DISMAX")
    if course_quality:
        search_term.add_filter(NumericFilter("course_quality", course_quality, 4))
    if course_difficulty:
        search_term.add_filter(NumericFilter("course_difficulty", course_difficulty, 4))
    if work_required:
        search_term.add_filter(NumericFilter("course_difficulty", 0, course_difficulty))

    results = r.ft("courses").search(search_term.with_scores())
    out = [
        {
            'code': e.code,
            'crosslistings': e.crosslistings,
            'instructors': e.instructors,
            'title': e.title,
            'description': e.description,
            'semester': e.semester,
            'course_quality': e.course_quality,
            'work_required': e.work_required,
            'difficulty': e.difficulty
        } for e in results.docs
    ]

    return Response(out)