from dateutil.tz import gettz
from django.db.models import F, OuterRef, Q, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Department, Instructor, Restriction, Section
from courses.util import get_current_semester, get_or_create_add_drop_period
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from PennCourses.settings.base import (
    PERMIT_REGISTRATION_RESTRICTION_CODES,
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
)
from review.models import ALL_FIELD_SLUGS, Review
from review.util import (
    aggregate_reviews,
    avg_and_recent_demand_plots,
    avg_and_recent_percent_open_plots,
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
    & Q(status_updates__section_id=F("id"))  # Filter out sections with no status updates
    & ~Q(
        id__in=Subquery(
            Restriction.objects.filter(code__in=PERMIT_REGISTRATION_RESTRICTION_CODES).values_list(
                "sections__id", flat=True
            )
        )
    )  # Filter out sections that require permit for registration
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
        & Q(course__semester__lt=current_semester)  # Filter our sections from the current semester
        & (
            Q(
                id__in=Subquery(
                    Review.objects.filter(responses__gt=0).values_list("section__id", flat=True)
                )
            )
        )  # Filter out sections that do not have review data
    )


course_filters_pcr = (~Q(title="")) | (~Q(description="")) | Q(sections__review__isnull=False)


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
    Get all reviews for a given course and other relevant information.
    Different aggregation views are provided, such as reviews spanning all semesters,
    only the most recent semester, and instructor-specific views.
    """
    if not Course.objects.filter(
        course_filters_pcr, sections__review__isnull=False, full_code=course_code
    ).exists():
        raise Http404()

    reviews = (
        review_averages(
            Review.objects.filter(section__course__full_code=course_code, responses__gt=0),
            {"review_id": OuterRef("id")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
            section_subfilters={"id": OuterRef("section_id")},
        )
        .annotate(
            course_title=F("section__course__title"),
            semester=F("section__course__semester"),
            instructor_name=F("instructor__name"),
        )
        .values()
    )

    instructors = aggregate_reviews(reviews, "instructor_id", name="instructor_name")

    course_qs = annotate_average_and_recent(
        Course.objects.filter(course_filters_pcr, full_code=course_code).order_by("-semester")[:1],
        match_on=Q(section__course__full_code=course_code),
        extra_metrics=True,
        section_subfilters={"course__full_code": course_code},
    )

    course = dict(course_qs[:1].values()[0])

    return Response(
        {
            "code": course["full_code"],
            "name": course["title"],
            "description": course["description"],
            "aliases": [c["full_code"] for c in course_qs[0].crosslistings.values("full_code")],
            "num_sections": Section.objects.filter(
                course__full_code=course_code, review__isnull=False, review__responses__gt=0
            )
            .values("full_code", "course__semester")
            .distinct()
            .count(),
            "num_sections_recent": Section.objects.filter(
                course__full_code=course_code,
                course__semester=course["recent_semester_calc"],
                review__isnull=False,
                review__responses__gt=0,
            )
            .values("full_code", "course__semester")
            .distinct()
            .count(),
            "average_reviews": make_subdict("average_", course),
            "recent_reviews": make_subdict("recent_", course),
            "num_semesters": course["average_semester_count"],
            "instructors": instructors,
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
        custom_path_parameter_desc={
            reverse_func("course-plots", args=["course_code"]): {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want plots for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    ),
                }
            },
        },
        override_response_schema=course_plots_response_schema,
    )
)
# @permission_classes([IsAuthenticated])
def course_plots(request, course_code):
    """
    Get all PCR plots for a given course.
    """
    if not Course.objects.filter(
        course_filters_pcr, sections__review__isnull=False, full_code=course_code
    ).exists():
        raise Http404()

    current_semester = get_current_semester()

    # Compute set of sections to include in plot data
    filtered_sections = (
        Section.objects.filter(
            extra_metrics_section_filters_pcr(current_semester), course__full_code=course_code,
        )
        .annotate(efficient_semester=F("course__semester"))
        .distinct()
    )
    instructor_ids = request.GET.get("instructor_ids")
    if instructor_ids:
        instructor_ids = [int(id) for id in instructor_ids.split(",")]
        filtered_sections = filtered_sections.filter(instructors__id__in=instructor_ids,)

    section_map = dict()  # a dict mapping semester to section id to section object
    for section in filtered_sections:
        if section.efficient_semester not in section_map:
            section_map[section.efficient_semester] = dict()
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
        match_on=Q(instructor_id=instructor_id),
        extra_metrics=True,
        section_subfilters={"instructors__id": instructor_id},
    )

    courses = annotate_average_and_recent(
        Course.objects.filter(
            course_filters_pcr,
            sections__review__isnull=False,
            sections__instructors__id=instructor_id,
        ).distinct(),
        match_on=Q(
            section__course__full_code=OuterRef(OuterRef("full_code")), instructor_id=instructor_id,
        ),
        extra_metrics=True,
        section_subfilters={
            "course__full_code": OuterRef("full_code"),
            "instructors__id": instructor_id,
        },
    )

    inst = instructor_qs.values()[0]

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": Section.objects.filter(
                instructors=instructor,
                course__semester=inst["recent_semester_calc"],
                review__isnull=False,
                review__responses__gt=0,
            ).count(),
            "num_sections": Section.objects.filter(
                instructors=instructor, review__isnull=False, review__responses__gt=0,
            ).count(),
            "average_reviews": make_subdict("average_", inst),
            "recent_reviews": make_subdict("recent_", inst),
            "num_semesters": inst["average_semester_count"],
            "courses": {
                r["full_code"]: {
                    "full_code": r["full_code"],
                    "average_reviews": make_subdict("average_", r),
                    "recent_reviews": make_subdict("recent_", r),
                    "latest_semester": r["recent_semester_calc"],
                    "num_semesters": r["average_semester_count"],
                    "code": r["full_code"],
                    "name": r["title"],
                }
                for r in courses.values()
            },
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
    reviews = (
        review_averages(
            Review.objects.filter(section__course__department=department, responses__gt=0),
            {"review_id": OuterRef("id")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
            section_subfilters={"id": OuterRef("section_id")},
        )
        .annotate(
            course_title=F("section__course__title"),
            course_code=F("section__course__full_code"),
            semester=F("section__course__semester"),
        )
        .values()
    )
    courses = aggregate_reviews(reviews, "course_code", code="course_code", name="course_title")

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
    Get the review history of an instructor teaching a course. No aggregations here.
    """
    instructor = get_object_or_404(Instructor, id=instructor_id)
    print([str(r) for r in Review.objects.filter(instructor_id=instructor_id, responses__gt=0)])
    reviews = review_averages(
        Review.objects.filter(
            section__course__full_code=course_code, instructor_id=instructor_id, responses__gt=0
        ),
        {"review_id": OuterRef("id")},
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
        section_subfilters={"id": OuterRef("section_id")},
    )
    reviews = reviews.annotate(
        course_title=F("section__course__title"), semester=F("section__course__semester"),
    )

    return Response(
        {
            "instructor": {"id": instructor_id, "name": instructor.name,},
            "course_code": course_code,
            "sections": [
                {
                    "course_name": review["course_title"],
                    "semester": review["semester"],
                    "forms_returned": review["responses"],
                    "forms_produced": review["enrollment"],
                    "ratings": make_subdict("bit_", review),
                    "comments": review["comments"],
                }
                for review in reviews.values()
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
        Course.objects.filter(course_filters_pcr, sections__review__isnull=False)
        .order_by("semester")
        .values("full_code", "title")
        .distinct()
    )
    course_set = [
        {
            "title": course["full_code"],
            "desc": [course["title"]],
            "url": f"/course/{course['full_code']}",
        }
        for course in courses
    ]
    departments = Department.objects.all().values("code", "name")
    department_set = [
        {"title": dept["code"], "desc": dept["name"], "url": f"/department/{dept['code']}",}
        for dept in departments
    ]

    instructors = Instructor.objects.filter(section__review__isnull=False).values(
        "name", "id", "section__course__department__code"
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
        {"title": v["title"], "desc": join_depts(v["desc"]), "url": v["url"],}
        for k, v in instructor_set.items()
    ]

    return Response(
        {"courses": course_set, "departments": department_set, "instructors": instructor_set}
    )
