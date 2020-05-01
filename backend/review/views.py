# from django.shortcuts import render
from django.db.models import F, Max, OuterRef, Q, Subquery
from rest_framework.decorators import api_view
from rest_framework.response import Response

from courses.models import Course, Instructor, review_averages
from review.models import Review


def make_subdict(field_prefix, d):
    r = dict()
    for k, v in d.items():
        if k.startswith(field_prefix):
            start_at = len(field_prefix)
            new_k = k[start_at:]
            r[new_k] = v
    return r


fields = ["course_quality", "difficulty", "instructor_quality"]


def annotate_with_matching_reviews(qs, match_on, most_recent=False, fields=None, prefix=""):
    matching_reviews = Review.objects.filter(match_on)
    if most_recent:
        # Filter the queryset to include only rows from the most recent semester.
        matching_reviews = matching_reviews.annotate(
            max_semester=Max("section__course__semester")
        ).filter(section__course__semester=F("max_semester"))

    return review_averages(
        qs, {"review__pk__in": Subquery(matching_reviews.values("pk"))}, fields, prefix,
    )


def annotate_average_and_recent(qs, match_on):
    qs = annotate_with_matching_reviews(qs, match_on, most_recent=False, prefix="average_")
    qs = annotate_with_matching_reviews(qs, match_on, most_recent=True, prefix="recent_")
    return qs


@api_view(["GET"])
def course_reviews(request, course_code):
    qs = annotate_average_and_recent(
        Course.objects.filter(full_code=course_code).order_by("-semester")[:1],
        match_on=Q(section__course__full_code=OuterRef(OuterRef("full_code"))),
    )
    c = qs.values()[0]

    insns = annotate_average_and_recent(
        Instructor.objects.filter(section__course__full_code=course_code).distinct(),
        match_on=Q(section__course__full_code=course_code, instructor__pk=OuterRef(OuterRef("pk"))),
    )

    iss = {
        i["name"]: {
            "name": i["name"],
            "average_reviews": make_subdict("average_", i),
            "recent_reviews": make_subdict("recent_", i),
        }
        for i in insns.values()
    }

    return Response(
        {
            "average_reviews": make_subdict("average_", c),
            "recent_reviews": make_subdict("recent_", c),
            "instructors": iss,
        }
    )


# Create your views here.
