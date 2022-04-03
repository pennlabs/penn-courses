from collections import defaultdict

from dateutil.tz import gettz
from django.db.models import (
    BooleanField,
    Case,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Department, Instructor, Restriction, Section
from courses.util import get_current_semester, get_or_create_add_drop_period
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from PennCourses.settings.base import (
    PERMIT_REQ_RESTRICTION_CODES,
    TIME_ZONE,
    WAITLIST_DEPARTMENT_CODES,
)
from review.annotations import annotate_average_and_recent, review_averages
from review.documentation import (
    autocomplete_response_schema,
    course_plots_response_schema,
    course_reviews_response_schema,
    department_reviews_response_schema,
    instructor_for_course_reviews_response_schema,
    instructor_reviews_response_schema,
    ACTIVITY_CHOICES,
)
from review.models import ALL_FIELD_SLUGS
from review.util import (
    avg_and_recent_demand_plots,
    avg_and_recent_percent_open_plots,
    get_average_and_recent_dict,
    get_average_and_recent_dict_list,
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
    & Q(capacity__isnull=False, capacity__gt=0)
    & ~Q(course__semester__icontains="b")  # Filter out summer classes
    & Q(status_updates__isnull=False)  # Filter out sections with no status updates
    & ~Q(
        id__in=Subquery(
            Restriction.objects.filter(code__in=PERMIT_REQ_RESTRICTION_CODES).values("sections__id")
        )
    )  # Filter out sections that require permit for registration
)


course_filters_pcr_allow_xlist = (
    ~Q(title="") | ~Q(description="") | Q(sections__review__isnull=False)
)
course_is_primary = Q(primary_listing__isnull=True) | Q(primary_listing_id=F("id"))
course_filters_pcr = course_is_primary & course_filters_pcr_allow_xlist

section_is_primary = Q(course__primary_listing__isnull=True) | Q(
    course__primary_listing_id=F("course_id")
)
section_filters_pcr = (
    section_is_primary
    & (~Q(course__title="") | ~Q(course__description="") | Q(review__isnull=False))
    & ~Q(activity="REC")
    & (~Q(status="X") | Q(review__isnull=False))
)

review_filters_pcr = Q(section__course__primary_listing__isnull=True) | Q(
    section__course__primary_listing_id=F("section__course_id")
)

reviewbit_filters_pcr = Q(review__section__course__primary_listing__isnull=True) | Q(
    review__section__course__primary_listing_id=F("review__section__course_id")
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
        & section_is_primary
        & Q(course__semester__lt=current_semester)
        & (~Q(status="X") | Q(review__isnull=False))
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
            Course.objects.filter(course_filters_pcr, full_code=course_code)
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

    instructors_qs = annotate_average_and_recent(
        Instructor.objects.filter(
            id__in=Subquery(
                Section.objects.filter(section_filters_pcr, course__topic=topic).values(
                    "instructors__id"
                )
            )
        ).distinct(),
        match_review_on=Q(
            section__course__topic=topic,
            instructor_id=OuterRef(OuterRef("id")),
        )
        & review_filters_pcr,
        match_section_on=Q(
            course__topic=topic,
            instructors__id=OuterRef(OuterRef("id")),
        )
        & section_filters_pcr,
        extra_metrics=True,
    )

    course_qs = annotate_average_and_recent(
        Course.objects.filter(course_filters_pcr, topic=topic).order_by("-semester")[:1],
        match_review_on=Q(section__course__topic=topic) & review_filters_pcr,
        match_section_on=Q(course__topic=topic) & section_filters_pcr,
        extra_metrics=True,
    )
    course = get_single_dict_from_qs(course_qs)

    num_registration_metrics = (
        Section.objects.filter(
            extra_metrics_section_filters_pcr(),
            course__topic=topic,
        )
        .annotate(
            has_registration_metrics=Case(
                When(extra_metrics_section_filters, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .aggregate(num=Sum("has_registration_metrics"))["num"]
        or 0
    )

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
            "num_sections": num_sections,
            "num_sections_recent": num_sections_recent,
            "instructors": get_average_and_recent_dict_list(
                instructors_qs.values(), "id", extra_fields=["id", "name"]
            ),
            "registration_metrics": num_registration_metrics > 0,
            **get_average_and_recent_dict(course),
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
    if len(section_map.keys()) > 0:
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

    courses_res = dict()
    max_sem = dict()
    for r in courses.values():
        full_code = r["most_recent_full_code"]
        if full_code not in max_sem or max_sem[full_code] < r["semester"]:
            max_sem[full_code] = r["semester"]
            courses_res[full_code] = get_average_and_recent_dict(
                r, full_code="most_recent_full_code", code="most_recent_full_code", name="title"
            )

    course_ids_subquery = Subquery(
        Course.objects.filter(
            course_filters_pcr,
            sections__instructors__id=instructor_id,
        ).values("id")
    )

    num_sections, num_sections_recent = get_num_sections(
        section_filters_pcr,
        course_id__in=course_ids_subquery,
    )

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": num_sections_recent,
            "num_sections": num_sections,
            "courses": courses_res,
            **get_average_and_recent_dict(inst),
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

    courses = annotate_average_and_recent(
        Course.objects.filter(
            course_filters_pcr_allow_xlist, department=department, topic__most_recent_id=F("id")
        ).distinct(),
        match_review_on=Q(
            section__course__topic=OuterRef(OuterRef("topic")),
        )
        & review_filters_pcr,
        match_section_on=Q(
            course__topic=OuterRef(OuterRef("topic")),
        )
        & section_filters_pcr,
        extra_metrics=True,
    )

    return Response(
        {
            "code": department.code,
            "name": department.name,
            "courses": {
                r["full_code"]: get_average_and_recent_dict(
                    r, full_code="full_code", code="full_code", name="title"
                )
                for r in courses.values()
                if r["average_semester_count"] > 0
            },
        }
    )


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
            Course.objects.filter(course_filters_pcr, full_code=course_code)
            .order_by("-semester")[:1]
            .select_related("topic", "topic__most_recent")
            .get()
        )
    except Course.DoesNotExist:
        raise Http404()

    instructor = get_object_or_404(Instructor, id=instructor_id)

    topic = course.topic
    course = course.topic.most_recent

    sections = review_averages(
        Section.objects.filter(
            section_filters_pcr,
            course__topic=topic,
            instructors__id=instructor_id,
        ).distinct(),
        reviewbit_subfilters=Q(review__section_id=OuterRef("id")),
        section_subfilters=Q(id=OuterRef("id")),
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    )
    sections = sections.annotate(
        course_code=F("course__full_code"),
        course_title=F("course__title"),
        efficient_semester=F("course__semester"),
        has_reviews=Case(
            When(Q(review__isnull=False), then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        comments=Coalesce("review__comments", Value(None)),
        responses=Coalesce("review__responses", Value(None)),
        enrollment=Coalesce("review__enrollment", Value(None)),
    ).distinct()

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
                    "forms_returned": section["responses"] if section["has_reviews"] else None,
                    "forms_produced": section["enrollment"] if section["has_reviews"] else None,
                    "ratings": make_subdict("bit_", section),
                    "comments": section["comments"],
                }
                for section in sections.values()
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
        Course.objects.filter(course_filters_pcr)
        .order_by("semester")
        .annotate(most_recent_full_code=F("topic__most_recent__full_code"))
        .values("full_code", "most_recent_full_code", "title")
        .distinct()
    )
    course_set = [
        {
            "title": course["full_code"],
            "most_recent_full_code": course["most_recent_full_code"],
            "desc": [course["title"]],
            "url": f"/course/{course['full_code']}",
        }
        for course in courses
    ]
    departments = Department.objects.all().values("code", "name")
    department_set = [
        {
            "title": dept["code"],
            "desc": dept["name"],
            "url": f"/department/{dept['code']}",
        }
        for dept in departments
    ]

    instructors = (
        Instructor.objects.filter(section__instructors__id=F("id"))
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

    instructor_set = [
        {
            "title": v["title"],
            "desc": join_depts(v["desc"]),
            "url": v["url"],
        }
        for k, v in instructor_set.items()
    ]

    return Response(
        {"courses": course_set, "departments": department_set, "instructors": instructor_set}
    )
