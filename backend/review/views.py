from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Department, Instructor, Section, StatusUpdate
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from review.annotations import annotate_average_and_recent, review_averages
from review.documentation import (
    autocomplete_response_schema,
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
    if not Course.objects.filter(sections__review__isnull=False, full_code=course_code).exists():
        raise Http404()

    reviews = (
        review_averages(
            Review.objects.filter(section__course__full_code=course_code),
            {"review_id": OuterRef("id")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
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
        Course.objects.filter(full_code=course_code).order_by("-semester")[:1],
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
        extra_metrics=True,
    )

    course = dict(course_qs[:1].values()[0])

    # Compute plots
    sections = Section.objects.filter(course__full_code=course_code).annotate(
        efficient_semester=F("course__semester")
    )
    section_map = dict()  # a dict mapping semester to section id to section object
    for section in sections:
        if section.efficient_semester not in section_map:
            section_map[section.efficient_semester] = dict()
        section_map[section.efficient_semester][section.id] = section
    avg_demand_plot, recent_demand_plot = avg_and_recent_demand_plots(section_map)
    avg_percent_open_plot, recent_percent_open_plot = avg_and_recent_percent_open_plots(section_map)

    return Response(
        {
            "code": course["full_code"],
            "name": course["title"],
            "description": course["description"],
            "aliases": [c["full_code"] for c in course_qs[0].crosslistings.values("full_code")],
            "num_sections": Section.objects.filter(
                course__full_code=course_code, review__isnull=False
            )
            .values("full_code", "course__semester")
            .distinct()
            .count(),
            "num_sections_recent": Section.objects.filter(
                course__full_code=course_code,
                course__semester=course["recent_semester_calc"],
                review__isnull=False,
            )
            .values("full_code", "course__semester")
            .distinct()
            .count(),
            "average_reviews": {
                **make_subdict("average_", course),
                "pca_demand_plot": avg_demand_plot,
                "percent_open_plot": avg_percent_open_plot,
            },
            "recent_reviews": {
                **make_subdict("recent_", course),
                "pca_demand_plot": recent_demand_plot,
                "percent_open_plot": recent_percent_open_plot,
            },
            "num_semesters": course["average_semester_count"],
            "instructors": instructors,
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
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    instructor_qs = annotate_average_and_recent(
        Instructor.objects.filter(pk=instructor.pk),
        match_on=Q(instructor_id=OuterRef(OuterRef("id"))),
        extra_metrics=True,
    )

    courses = annotate_average_and_recent(
        Course.objects.filter(
            sections__review__isnull=False, sections__instructors__id=instructor.id
        ).distinct(),
        match_on=Q(
            section__course__full_code=OuterRef(OuterRef("full_code")), instructor_id=instructor.id,
        ),
        extra_metrics=True,
    )

    inst = instructor_qs.values()[0]

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": Section.objects.filter(
                instructors=instructor, course__semester=inst["recent_semester_calc"]
            ).count(),
            "num_sections": Section.objects.filter(instructors=instructor).count(),
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
            Review.objects.filter(section__course__department=department),
            {"review_id": OuterRef("id")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
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
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    reviews = review_averages(
        Review.objects.filter(section__course__full_code=course_code, instructor=instructor),
        {"review_id": OuterRef("id")},
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    )
    reviews = reviews.annotate(
        course_title=F("section__course__title"),
        semester=F("section__course__semester"),
        section_capacity=F("section__capacity"),
        percent_open=F("section__percent_open"),
        num_openings=Coalesce(
            Subquery(
                StatusUpdate.objects.filter(
                    section__pk=OuterRef("section__pk"), in_add_drop_period=True
                )
                .values("pk")
                .annotate(count=Count("pk"))
                .values("count")
            ),
            Value(0),
        ),
    )

    return Response(
        {
            "instructor": {"id": instructor.pk, "name": instructor.name,},
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


# reverse_func("review-autocomplete")


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
        Course.objects.filter(sections__review__isnull=False)
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
