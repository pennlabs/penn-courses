from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    FloatField,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Cast

from PennCourses.settings.base import WAITLIST_DEPARTMENT_CODES
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


def review_averages(
    queryset, subfilters, fields=None, prefix="", semester_aggregations=False, extra_metrics=True
):
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
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment
        percentage, percent of add/drop period open, and average number of openings during add/drop
    """
    from courses.models import Restriction, StatusUpdate

    # ^ imported here to avoid circular imports

    if fields is None:
        fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]

    # Filters for sections to include in extra metric aggregations
    extra_metrics_filter = (
        ~Q(
            review__section__course__department__code__in=WAITLIST_DEPARTMENT_CODES
        )  # Manually filter out classes from depts with waitlist systems during add/drop
        & Q(
            review__section__capacity__isnull=False, review__section__capacity__gt=0,
        )  # Filter our sections with invalid capacity
        & ~Q(review__section__course__semester__icontains="b")  # Filter out summer classes
        & Q(
            review__section__status_updates__section_id=F("review__section_id")
        )  # Filter out sections with no status updates
        & ~Q(
            review__section_id__in=Subquery(
                Restriction.objects.filter(description__icontains="permission").values_list(
                    "sections__id", flat=True
                )
            )
        )  # Filter out classes with permit required for registration
    )  # If you modify these filters, reflect the same changes in these corresponding filters:
    # plots_base_section_filters in review/views/course_reviews

    class PercentOpenSubqueryAvg(Subquery):
        template = (
            "(SELECT AVG(percent_open_subquery_for_avg.percent_open_annotation) FROM (%(subquery)s)"
            " as percent_open_subquery_for_avg)"
        )

    class NumOpeningsSubqueryAvg(Subquery):
        template = (
            "(SELECT AVG(num_openings_subquery_for_avg.num_openings_annotation) FROM (%(subquery)s)"
            " as num_openings_subquery_for_avg)"
        )

    queryset = queryset.annotate(
        **{
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
            },
            **(
                {
                    (prefix + "final_enrollment_percentage"): Subquery(
                        ReviewBit.objects.filter(**subfilters)
                        .values("review_id", "review__enrollment", "review__section__capacity")
                        .order_by()
                        .distinct()
                        .annotate(
                            final_enrollment_percentage=Case(
                                When(
                                    Q(review__section__capacity__isnull=False)
                                    & Q(review__section__capacity__gt=0),
                                    then=Cast("review__enrollment", FloatField())
                                    / Cast("review__section__capacity", FloatField()),
                                ),
                                default_value=Value(None),
                                output_field=FloatField(),
                            ),
                            common=Value(1),
                        )
                        .values("common")
                        .annotate(
                            avg_final_enrollment_percentage=Avg("final_enrollment_percentage")
                        )
                        .values("avg_final_enrollment_percentage")[:1],
                        output_field=FloatField(),
                    ),
                    (prefix + "percent_open"): PercentOpenSubqueryAvg(
                        ReviewBit.objects.filter(extra_metrics_filter, **subfilters)
                        .values("review__section_id", "review__section__percent_open")
                        .order_by()
                        .distinct()
                        .annotate(percent_open_annotation=Avg("review__section__percent_open")),
                        output_field=FloatField(),
                    ),
                    (prefix + "num_openings"): NumOpeningsSubqueryAvg(
                        ReviewBit.objects.filter(extra_metrics_filter, **subfilters)
                        .values("review__section_id")
                        .order_by()
                        .distinct()
                        .annotate(
                            num_openings_annotation=Subquery(
                                StatusUpdate.objects.filter(
                                    new_status="O", section_id=OuterRef("review__section__id")
                                )
                                .annotate(common=Value(1))
                                .values("common")
                                .annotate(count=Count("*"))
                                .values("count")[:1],
                                output_field=IntegerField(),
                            )
                        ),
                        output_field=FloatField(),
                    ),
                }
                if extra_metrics
                else dict()
            ),
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


def annotate_with_matching_reviews(
    qs, match_on, most_recent=False, fields=None, prefix="", extra_metrics=True
):
    """
    Annotate each element the passed-in queryset with a subset of all review averages.
    :param qs: queryset to annotate.
    :param match_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param most_recent: If `True`, only aggregate results for the most recent semester.
    :param fields: list of fields to aggregate.
    :param prefix: prefix of annotated fields on the queryset.
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment
        percentage, percent of add/drop period open, and average number of openings during add/drop
    """

    if fields is None:
        fields = ALL_FIELD_SLUGS

    matching_reviews = Review.objects.filter(match_on)
    filters = {"review_id__in": Subquery(matching_reviews.values("id"))}
    if most_recent:
        # Filter the queryset to include only rows from the most recent semester.
        filters["review__section__course__semester"] = Subquery(
            matching_reviews.annotate(common=Value(1))
            .values("common")
            .annotate(max_semester=Max("section__course__semester"))
            .values("max_semester")[:1]
        )

    return review_averages(
        qs, filters, fields, prefix, semester_aggregations=True, extra_metrics=extra_metrics
    )


def annotate_average_and_recent(qs, match_on, extra_metrics=True):
    """
    Annotate queryset with both all reviews and recent reviews.
    :param qs: Queryset to annotate.
    :param match_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment
        percentage, percent of add/drop period open, and average number of openings during add/drop
    """
    qs = annotate_with_matching_reviews(
        qs, match_on, most_recent=False, prefix="average_", extra_metrics=extra_metrics
    )
    qs = annotate_with_matching_reviews(
        qs, match_on, most_recent=True, prefix="recent_", extra_metrics=extra_metrics
    )
    return qs
