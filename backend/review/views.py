from typing import Dict, List

from django.db.models import F, OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from PennCourses.docs_settings import PcxAutoSchema
from courses.models import Course, Department, Instructor, Section
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


def dict_average(entries: List[Dict[str, int]]) -> Dict[str, int]:
    keys = []
    for entry in entries:
        keys.extend(entry.keys())
    keys = set(keys)

    averages = {k: (0, 0) for k in keys}
    for entry in entries:
        for k, v in entry.items():
            sum_, count_ = averages[k]
            averages[k] = (sum_ + v, count_ + 1)

    return {k: v[0] / v[1] if v[1] > 0 else 0 for k, v in averages.items()}


def nest_related(nested_data, nested_key, other_fields):
    """
    Return all nested data necessary for PCR views.

    :param nested_data: ValuesQuerySet (or just a dict) to nest.
    :param nested_key: Property which represents unique identifier of each row.
    :param other_fields: the key will be the key in each element's dictionary.
    The value is the lookup value in the input row.
    """
    return {
        r[nested_key]: {
            nested_key: r[nested_key],
            "average_reviews": make_subdict("average_", r),
            "recent_reviews": make_subdict("recent_", r),
            **{k: r[v] for k, v in other_fields.items()},
        }
        for r in nested_data
    }


def make_review_response(top_level, nested, nested_name, nested_key, other_keys=dict()):
    """
    Instructor and course responses are formatted exactly the same. Factor out the
    response to remove duplicated code.
    """
    return {
        "average_reviews": make_subdict("average_", top_level),
        "recent_reviews": make_subdict("recent_", top_level),
        "num_semesters": top_level["average_semester_count"],
        nested_name: nest_related(
            nested,
            nested_key,
            {
                "latest_semester": "recent_semester_calc",
                "num_semesters": "average_semester_count",
                **other_keys,
            },
        ),
    }


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
@schema(PcxAutoSchema())
@permission_classes([IsAuthenticated])
def course_reviews(request, course_code):
    """
    Get all reviews for a given course, aggregated by instructor.
    """
    if not Course.objects.filter(full_code=course_code).exists():
        raise Http404()

    course_qs = annotate_average_and_recent(
        Course.objects.filter(full_code=course_code).order_by("-semester")[:1],
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    )

    course = dict(course_qs[:1].values()[0])

    # We could use `annotate_average_and_recent` for instructor reviews as well, but aggregating
    # every instructor is a very slow query. So, instead, we grab the "flat" reviews,
    # and aggregate them in Python code.

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

    reviews_by_instructor = dict()
    for review in reviews:
        instructor = review["instructor_id"]
        if instructor not in reviews_by_instructor:
            reviews_by_instructor[instructor] = []

        reviews_by_instructor[instructor].append(
            {
                "instructor_name": review["instructor_name"],
                "semester": review["semester"],
                "scores": make_subdict("bit_", review),
            }
        )

    instructors = dict()
    for k, reviews in reviews_by_instructor.items():
        latest_sem = max([r["semester"] for r in reviews])
        all_scores = [r["scores"] for r in reviews]
        recent_scores = [r["scores"] for r in reviews if r["semester"] == latest_sem]
        instructors[k] = {
            "id": k,
            "average_reviews": dict_average(all_scores),
            "recent_reviews": dict_average(recent_scores),
            "name": reviews[0]["instructor_name"],
            "latest_semester": latest_sem,
            "num_semesters": len(set([r["semester"] for r in reviews])),
        }

    return Response(
        {
            "code": course["full_code"],
            "name": course["title"],
            "description": course["description"],
            "aliases": [c["full_code"] for c in course_qs[0].crosslistings.values("full_code")],
            "num_sections": Section.objects.filter(
                course__full_code=course_code, review__isnull=False
            ).count(),
            "num_sections_recent": Section.objects.filter(
                course__full_code=course_code,
                course__semester=course["recent_semester_calc"],
                review__isnull=False,
            ).count(),
            "average_reviews": make_subdict("average_", course),
            "recent_reviews": make_subdict("recent_", course),
            "num_semesters": course["average_semester_count"],
            "instructors": instructors,
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
        Course.objects.filter(sections__instructors__pk=instructor.pk).distinct(),
        match_on=Q(
            section__course__full_code=OuterRef(OuterRef("full_code")),
            instructor__pk=instructor.pk,
        ),
    )

    inst = instructor_qs.values()[0]

    review_response = make_review_response(
        inst, courses.values(), "courses", "full_code", {"code": "full_code", "name": "title"},
    )

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": Section.objects.filter(
                instructors=instructor, course__semester=inst["recent_semester_calc"]
            ).count(),
            "num_sections": Section.objects.filter(instructors=instructor).count(),
            **review_response,
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
    # courses = annotate_average_and_recent(
    #     Course.objects.filter(department=department).values("full_code", "title"),
    #     match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    # )
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

    reviews_by_course = dict()
    for review in reviews:
        course = review["course_code"]
        if course not in reviews_by_course:
            reviews_by_course[course] = []

        reviews_by_course[course].append(
            {
                "code": review["course_code"],
                "title": review["course_title"],
                "semester": review["semester"],
                "scores": make_subdict("bit_", review),
            }
        )

    courses = dict()
    for k, reviews in reviews_by_course.items():
        latest_sem = max([r["semester"] for r in reviews])
        all_scores = [r["scores"] for r in reviews]
        recent_scores = [r["scores"] for r in reviews if r["semester"] == latest_sem]
        courses[k] = {
            "code": k,
            "name": reviews[0]["title"],
            "average_reviews": dict_average(all_scores),
            "recent_reviews": dict_average(recent_scores),
            "latest_semester": latest_sem,
            "num_semesters": len(set([r["semester"] for r in reviews])),
        }

    return Response(
        {
            "code": department.code,
            "name": department.name,
            "courses": courses
            # "courses": nest_related(courses, "full_code", {"code": "full_code", "name": "title"}),
        }
    )


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
@schema(PcxAutoSchema())
def autocomplete(request):
    """
    Courses, departments, instructors. All objects are title, desc, url.
    """

    courses = Course.objects.filter().values("full_code", "title")
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

    instructors = Instructor.objects.all().values("name", "id", "section__course__department__code")
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
