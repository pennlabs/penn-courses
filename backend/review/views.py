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
from review.models import ALL_FIELD_SLUGS, Review, REVIEW_BIT_LABEL
from review.util import aggregate_reviews, make_subdict, to_r_camel

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
                        "The dash-joined department and code of the course you are requesting review for, e.g. `CIS-120` for CIS-120."
                    )
                }
            },
        },
        override_schema={
            reverse_func("course-reviews", args=["course_code"]): {
                "GET": {
                    200: {
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The dash-joined department and code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                            },
                            "name": {
                                "type": "string",
                                "description": "The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.",  # noqa E501
                            },
                            "description": {
                                "type": "string",
                                "description": "The description of the course, e.g. 'A fast-paced introduction to the fundamental concepts of programming... [etc.]' for CIS-120.",  # noqa E501
                            },
                            "aliases": {
                                "type": "array",
                                "description": "A list of courses that are crosslisted with this course.",  # noqa E501
                                "items": {
                                    "type": "string",
                                    "description": "The dash-joined department and code of a crosslisting.",  # noqa E501
                                },
                            },
                            "num_sections": {
                                "type": "integer",
                                "description": "The number of sections belonging to this course across all semesters.",  # noqa E501
                            },
                            "num_sections_recent": {
                                "type": "integer",
                                "description": "The number of sections belonging to this course in its most recent semester.",  # noqa E501
                            },
                            "average_reviews": {
                                "type": "object",
                                "description": "This course's average reviews across all of its sections from all semesters.",  # noqa E501
                                "properties": {
                                    to_r_camel(bit_label[2]): {
                                        "type": "number",
                                        "description": f"Average {bit_label[1]}"
                                    }
                                    for bit_label in REVIEW_BIT_LABEL
                                }
                            },
                            "recent_reviews": {
                                "type": "object",
                                "description": "This course's average reviews across all of its sections from the most recent semester.",  # noqa E501
                                "properties": {
                                    to_r_camel(bit_label[2]): {
                                        "type": "number",
                                        "description": f"Average {bit_label[1]}"
                                    }
                                    for bit_label in REVIEW_BIT_LABEL
                                }
                            },
                            "num_semesters": {"type": "integer", "description": "The number of semesters from which this course has reviews."},
                            # "instructors": {"type": "", "description": ""},
                        }
                    },
                }
            },
        },
    )
)
@permission_classes([IsAuthenticated])
def course_reviews(request, course_code):
    """
    Get all reviews for a given course, aggregated by instructor.
    """
    if not Course.objects.filter(sections__review__isnull=False, full_code=course_code).exists():
        raise Http404()

    reviews = (
        review_averages(
            Review.objects.filter(section__course__full_code=course_code),
            {"review__pk": OuterRef("pk")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
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
    )

    course = dict(course_qs[:1].values()[0])

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
            "average_reviews": make_subdict("average_", course),
            "recent_reviews": make_subdict("recent_", course),
            "num_semesters": course["average_semester_count"],
            "instructors": instructors,
            # TODO: add visualizations data
        }
    )


@api_view(["GET"])
@schema(PcxAutoSchema())
@permission_classes([IsAuthenticated])
def instructor_reviews(request, instructor_id):
    """
    Get all reviews for a given instructor, aggregated by course.
    """
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    instructor_qs = annotate_average_and_recent(
        Instructor.objects.filter(pk=instructor.pk),
        match_on=Q(instructor__pk=OuterRef(OuterRef("pk"))),
    )

    courses = annotate_average_and_recent(
        Course.objects.filter(
            sections__review__isnull=False, sections__instructors__pk=instructor.pk
        ).distinct(),
        match_on=Q(
            section__course__full_code=OuterRef(OuterRef("full_code")),
            instructor__pk=instructor.pk,
        ),
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
@schema(PcxAutoSchema())
@permission_classes([IsAuthenticated])
def department_reviews(request, department_code):
    """
    Get reviews for all courses in a department.
    """
    department = get_object_or_404(Department, code=department_code)
    reviews = (
        review_averages(
            Review.objects.filter(section__course__department=department),
            {"review__pk": OuterRef("pk")},
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
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
@schema(PcxAutoSchema())
@permission_classes([IsAuthenticated])
def instructor_for_course_reviews(request, course_code, instructor_id):
    """
    Get the review history of an instructor teaching a course. No aggregations here.
    """
    instructor = get_object_or_404(Instructor, pk=instructor_id)
    reviews = review_averages(
        Review.objects.filter(section__course__full_code=course_code, instructor=instructor),
        {"review__pk": OuterRef("pk")},
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
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
                    # Below are new metrics
                    "final_enrollment_percentage": (
                        review["enrollment"] / review["section_capacity"]
                        if review["enrollment"] is not None
                        and review["section_capacity"] is not None
                        and review["section_capacity"] > 0
                        else None
                    ),
                    "percent_open": review["percent_open"],
                    "num_openings": review["num_openings"],
                }
                for review in reviews.values()
            ],
        }
    )


@api_view(["GET"])
@schema(PcxAutoSchema())
def autocomplete(request):
    """
    Autocomplete entries for Courses, departments, instructors. All objects have title, description,
    and url.
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
