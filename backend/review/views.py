from django.db.models import F, OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from options.models import get_value
from rest_framework.decorators import api_view
from rest_framework.response import Response

from courses.models import Course, Department, Instructor
from review.annotations import annotate_average_and_recent, review_averages
from review.models import ALL_FIELD_SLUGS, Review


def to_r_camel(s):
    """
    Turns fields from python snake_case to the PCR frontend's rCamelCase.
    """
    return "r" + "".join([x.title() for x in s.split("_")])


def make_subdict(field_prefix, d):
    """
    Rows in a queryset that don't represent related database models are flat. But we want
    our JSON to have a nested structure that makes more sense to the client. This function
    takes fields from a flat dictionary with a certain prefix
    """
    start_at = len(field_prefix)
    return {
        to_r_camel(k[start_at:]): v
        for k, v in d.items()
        if k.startswith(field_prefix) and v is not None
    }


def make_list_response(nested_data, nested_key, other_fields):
    return {
        r[nested_key]: {
            nested_key: r[nested_key],
            "average_reviews": make_subdict("average_", r),
            "recent_reviews": make_subdict("recent_", r),
            **{k: r[v] for k, v in other_fields.items()},
        }
        for r in nested_data
    }


def make_review_response(top_level, nested, nested_name, nested_key):
    """
    Instructor and course responses are formatted exactly the same. Factor out the
    response to remove duplicated code.
    """
    return Response(
        {
            "average_reviews": make_subdict("average_", top_level),
            "recent_reviews": make_subdict("recent_", top_level),
            "num_semesters": top_level["average_semester_count"],
            nested_name: make_list_response(
                nested,
                nested_key,
                {
                    "latest_semester": "recent_semester_calc",
                    "num_semesters": "average_semester_count",
                },
            )
        }
    )


@api_view(["GET"])
def course_reviews(request, course_code):
    """
    Get all reviews for a given course, aggregated by instructor.
    """
    if not Course.objects.filter(full_code=course_code).exists():
        raise Http404()
    course = annotate_average_and_recent(
        Course.objects.filter(full_code=course_code).order_by("-semester")[:1],
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    )

    instructors = annotate_average_and_recent(
        Instructor.objects.filter(section__course__full_code=course_code).distinct(),
        match_on=Q(section__course__full_code=course_code, instructor__pk=OuterRef(OuterRef("pk"))),
    )

    return make_review_response(course.values()[0], instructors.values(), "instructors", "name")


@api_view(["GET"])
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
        Course.objects.filter(sections__instructors__pk=instructor.pk).distinct(),
        match_on=Q(
            section__course__full_code=OuterRef(OuterRef("full_code")),
            instructor__pk=instructor.pk,
        ),
    )
    return make_review_response(instructor_qs.values()[0], courses.values(), "courses", "full_code")


@api_view(["GET"])
def department_reviews(request, department_code):
    """
    Get reviews for all courses in a department.
    """
    department = get_object_or_404(Department, code=department_code)
    courses = annotate_average_and_recent(
        Course.objects.filter(department=department).values("full_code", "title"),
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    )
    return Response(
        {
            "code": department.code,
            "name": department.name,
            "courses": make_list_response(courses, "full_code", {"code": "full_code", "name": "title"})
        }
    )


@api_view(["GET"])
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
        course_title=F("section__course__title"), semester=F("section__course__semester")
    )

    return Response(
        {
            "instructor": {"id": instructor.pk, "name": instructor.name,},
            "course_code": course_code,
            "sections": [
                {
                    "course_name": review["course_title"],
                    "semester": review["semester"],
                    "ratings": make_subdict("bit_", review),
                }
                for review in reviews.values()
            ],
        }
    )


@api_view(["GET"])
def autocomplete(request):
    """
    Courses, departments, instructors. All objects are title, desc, url.
    """

    courses = Course.objects.filter(semester=get_value("SEMESTER")).values("full_code", "title")
    course_set = [
        {
            "title": course["full_code"],
            "desc": [course["title"]],
            "url": reverse("course-reviews", args=[course["full_code"]]),
        }
        for course in courses
    ]
    departments = Department.objects.all().values("code", "name")
    department_set = [
        {
            "title": dept["code"],
            "desc": dept["name"],
            "url": reverse("department-reviews", args=[dept["code"]]),
        }
        for dept in departments
    ]

    instructors = Instructor.objects.all().values("name", "id", "section__course__department__code")
    instructor_set = {}
    for inst in instructors:
        if inst["id"] not in instructor_set:
            instructor_set[inst["id"]] = {
                "title": inst["name"],
                "desc": set([inst["section__course__department__code"]]),
                "url": reverse("instructor-reviews", args=[inst["id"]]),
            }
        instructor_set[inst["id"]]["desc"].add(inst["section__course__department__code"])
    instructor_set = [
        {"title": v["title"], "desc": ",".join(sorted(list(v["desc"]))), "url": v["url"],}
        for k, v in instructor_set.items()
    ]

    return Response(
        {"courses": course_set, "departments": department_set, "instructors": instructor_set}
    )
