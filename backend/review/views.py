from django.db.models import F, Max, OuterRef, Q, Subquery, Value
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from courses.models import Course, Department, Instructor, review_averages
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


def annotate_with_matching_reviews(qs, match_on, most_recent=False, fields=None, prefix=""):
    """
    Annotate each element the passed-in queryset with a subset of all review averages.
    :param qs: queryset to annotate.
    :param match_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param most_recent: If `True`, only aggregate results for the most recent semester.
    :param fields: list of fields to aggregate.
    :param prefix: prefix of annotated fields on the queryset.
    """

    if fields is None:
        fields = ALL_FIELD_SLUGS

    matching_reviews = Review.objects.filter(match_on)
    filters = {"review__pk__in": Subquery(matching_reviews.values("pk"))}
    if most_recent:
        # Filter the queryset to include only rows from the most recent semester.
        filters["review__section__course__semester"] = Subquery(
            matching_reviews.annotate(common=Value(1))
            .values("common")
            .annotate(max_semester=Max("section__course__semester"))
            .values("max_semester")[:1]
        )

    return review_averages(qs, filters, fields, prefix, semester_aggregations=True)


def annotate_average_and_recent(qs, match_on):
    """
    Annotate queryset with both all reviews and recent reviews.
    :param qs: Queryset to annotate.
    :param match_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    """
    qs = annotate_with_matching_reviews(qs, match_on, most_recent=False, prefix="average_")
    qs = annotate_with_matching_reviews(qs, match_on, most_recent=True, prefix="recent_")
    return qs


def make_review_response(top_level, nested, nested_name, nested_key):
    return Response(
        {
            "average_reviews": make_subdict("average_", top_level),
            "recent_reviews": make_subdict("recent_", top_level),
            "num_semesters": top_level["average_semester_count"],
            nested_name: {
                r[nested_key]: {
                    nested_key: r[nested_key],
                    "average_reviews": make_subdict("average_", r),
                    "recent_reviews": make_subdict("recent_", r),
                    "latest_semester": r["recent_semester_calc"],
                    "num_semesters": r["average_semester_count"],
                }
                for r in nested
            },
        }
    )


@api_view(["GET"])
def course_reviews(request, course_code):
    """
    Get all reviews for a given course, aggregated by instructor.
    """
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
        Course.objects.filter(section__instructor__pk=instructor.pk),
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
        Course.objects.filter(department=department).values("full_code", "name"),
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    )
    return Response(
        {
            "code": department.code,
            "name": department.name,
            "courses": [
                {
                    "code": course["full_code"],
                    "name": course["name"],
                    "average_reviews": make_subdict(course, "average_"),
                    "recent_reviews": make_subdict(course, "recent_"),
                }
                for course in courses
            ],
        }
    )


@api_view(["GET"])
def instructor_for_course_reviews(request, course_code, instructor_id):
    instructor = get_object_or_404(Instructor, instructor_id)
    reviews = review_averages(
        Review.objects.filter(section__course__full_code=course_code, instructor=instructor),
        {"review__pk": OuterRef("pk")},
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
    )
    reviews = reviews.annotate(
        course_name=F("section__course__name"), semester=F("section__course__semester")
    )

    return Response(
        {
            "instructor": {"id": instructor.pk, "name": instructor.name,},
            "course_code": course_code,
            "sections": [
                {
                    "course_name": review["course_name"],
                    "semester": review["semester"],
                    "ratings": make_subdict("bit_", review),
                }
                for review in reviews.values()
            ],
        }
    )


@api_view(["GET"])
def live_course(request, course_code):
    # semester = "2020C"
    # course = get_object_or_404(Course, full_code=course_code, semester=semester)
    pass


@api_view(["GET"])
def autocomplete(request):
    """
    Courses, departments, instructors. All objects are title, desc, url.
    """
    pass
