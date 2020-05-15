from django.db.models import Avg, Count, FloatField, Max, Subquery, Value

from review.models import ALL_FIELD_SLUGS, Review, ReviewBit


"""
Queryset annotations
====================

Actual review data is stored in an Entity-Attribute-Value (EAV) format in the ReviewBit
model. This means that getting associated review data for a queryset requires a few
JOINs under the hood. Doing aggregations on these ReviewBits also requires the explicit
use of subqueries. You can read about Subqueries here:
https://docs.djangoproject.com/en/2.2/ref/models/expressions/#subquery-expressions.

In short, however, subqueries allow us to query for review data from the ReviewBit table
*inside* any other queryset to use in aggregations and annotations. We can filter down
the ReviewBits that we want to aggregate based on their field name, along with any other
Django filter query that can be different *per row* in the outer query. To match on fields
from the outer query, we use the OuterRef() expressions.

This allows us to have the database do all of the work of averaging PCR data. Were we to do
this aggregation all in Python code, it would likely take many more queries (read: round-trips to
the DB), be *much* slower, and require cacheing.
"""


def review_averages(queryset, subfilters, fields=None, prefix="", semester_aggregations=False):
    """
    Annotate the queryset with the average of all ReviewBits matching the given subfilters.
    :param queryset: Queryset to annotate with averages.
    :param subfilters: Filters to filter down the ReviewBits used in each individual aggregation.
    use OuterRef() to refer to values in the outer queryset.
    :param fields: the ReviewBit fields to aggregate. if None, defaults to the four fields
    used in PCP.
    :param prefix: prefix for fields in annotated queryset. Useful when applying review_averages
    multiple times to the same queryset with different subfilters.
    :param semester_aggregations: option to annotate additional semester aggregations for the
    semester returned by the subfilters (only useful if subfilters filter down to one semester),
    as well as the count of the number of semesters included in the queryset's annotations.
    """
    if fields is None:
        fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]
    queryset = queryset.annotate(
        **{
            (prefix + field): Subquery(
                ReviewBit.objects.filter(field=field, **subfilters)
                .values("field")
                .order_by()
                .annotate(avg=Avg("average"))
                .values("avg")[:1],
                output_field=FloatField(),
            )
            for field in fields
        }
    )
    if semester_aggregations:
        queryset = queryset.annotate(
            **{
                (prefix + "semester_calc"): Subquery(
                    ReviewBit.objects.filter(**subfilters).values(
                        "review__section__course__semester"
                    )[:1]
                ),
                (prefix + "semester_count"): Subquery(
                    ReviewBit.objects.filter(**subfilters)
                    .values("field")
                    .order_by()
                    .annotate(count=Count("review__section__course__semester"))
                    .values("count")[:1]
                ),
            }
        )
    return queryset


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
