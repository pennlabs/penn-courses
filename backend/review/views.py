from django.db.models import Max, OuterRef, Q, Subquery, Value
from rest_framework.decorators import api_view
from rest_framework.response import Response

from courses.models import Course, Instructor, review_averages
from review.models import ALL_FIELD_SLUGS, Review


def to_r_camel(s):
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

    return review_averages(qs, filters, fields, prefix,)


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
