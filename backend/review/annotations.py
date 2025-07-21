from django.db.models import (
    Avg,
    Case,
    Count,
    FloatField,
    IntegerField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)

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
    queryset,
    reviewbit_subfilters,
    section_subfilters,
    fields=None,
    prefix="",
    semester_aggregations=False,
    extra_metrics=True,
):
    """
    Annotate the queryset with the average of all ReviewBits matching the given subfilters.
    :param queryset: Queryset to annotate with averages.
    :param reviewbit_subfilters: `Q()` expression to filter down the ReviewBits used in each
        individual aggregation. Use OuterRef() to refer to values in the outer queryset.
    :param: section_subfilters: The same as reviewbit_subfilters, but for filtering Sections.
    :param fields: the ReviewBit fields to aggregate. if None, defaults to the four fields
        used in PCP.
    :param prefix: prefix for fields in annotated queryset. Useful when applying review_averages
        multiple times to the same queryset with different subfilters.
    :param semester_aggregations: option to annotate additional semester aggregations for the
        semester returned by the subfilters (only useful if subfilters filter down to one semester),
        as well as the count of the number of semesters included in the queryset's annotations.
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment,
        percent of add/drop period open, average number of openings during add/drop,
        and percentage of sections filled in advance registration
    """
    from courses.models import Section, StatusUpdate
    from review.views import extra_metrics_section_filters_pcr

    # ^ imported here to avoid circular imports

    if fields is None:
        fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]

    class PercentOpenSubqueryAvg(Subquery):
        template = (
            "(SELECT AVG(percent_open) FROM (%(subquery)s) percent_open_avg_view)"
        )

    class NumOpeningsSubqueryAvg(Subquery):
        template = "(SELECT AVG(num_openings) FROM (%(subquery)s) num_openings_view)"

    class FilledInAdvRegAvg(Subquery):
        template = (
            "(SELECT AVG(filled_in_adv_reg) FROM (%(subquery)s) filled_in_adv_reg_view)"
        )

    queryset = queryset.annotate(
        **{
            **{
                (prefix + field): Subquery(
                    ReviewBit.objects.filter(
                        reviewbit_subfilters,
                        field=field,
                        review__responses__gt=0,
                    )
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
                    (prefix + "final_enrollment"): Subquery(
                        ReviewBit.objects.filter(
                            reviewbit_subfilters, review__responses__gt=0
                        )
                        .values(
                            "review_id",
                            "review__enrollment",
                            "review__section__capacity",
                        )
                        .order_by()
                        .distinct()
                        .annotate(common=Value(1))
                        .values("common")
                        .annotate(avg_final_enrollment=Avg("review__enrollment"))
                        .values("avg_final_enrollment")[:1],
                        output_field=FloatField(),
                    ),
                    (prefix + "percent_open"): PercentOpenSubqueryAvg(
                        Section.objects.filter(
                            extra_metrics_section_filters_pcr() & section_subfilters
                        )
                        .order_by()
                        .distinct(),
                        output_field=FloatField(),
                    ),
                    (prefix + "num_openings"): NumOpeningsSubqueryAvg(
                        Section.objects.filter(
                            extra_metrics_section_filters_pcr() & section_subfilters
                        )
                        .order_by()
                        .distinct()
                        .annotate(
                            num_openings=Subquery(
                                StatusUpdate.objects.filter(
                                    in_add_drop_period=True,
                                    new_status="O",
                                    section_id=OuterRef("id"),
                                )
                                .annotate(common=Value(1))
                                .values("common")
                                .order_by()
                                .annotate(count=Count("*"))
                                .values("count")[:1],
                                output_field=IntegerField(),
                            )
                        ),
                        output_field=FloatField(),
                    ),
                    (prefix + "filled_in_adv_reg"): FilledInAdvRegAvg(
                        Section.objects.filter(
                            extra_metrics_section_filters_pcr() & section_subfilters
                        )
                        .order_by()
                        .distinct()
                        .annotate(
                            filled_in_adv_reg=Subquery(
                                StatusUpdate.objects.filter(
                                    in_add_drop_period=False,
                                    percent_through_add_drop_period=0,
                                    section_id=OuterRef("id"),
                                )
                                .order_by("-created_at")
                                .annotate(
                                    filled=Case(
                                        When(
                                            Q(new_status="C"),
                                            then=Value(1.0),
                                        ),
                                        When(
                                            Q(new_status="O"),
                                            then=Value(0.0),
                                        ),
                                        output_field=FloatField(),
                                    )
                                )
                                .values("filled")[:1],
                                output_field=FloatField(),
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
                    Section.objects.filter(section_subfilters)
                    .values("course__semester")
                    .order_by("-course__semester")[:1]
                ),
                (prefix + "semester_count"): Subquery(
                    Section.objects.filter(section_subfilters)
                    .annotate(common=Value(1))
                    .values("common")
                    .annotate(count=Count("course__semester", distinct=True))
                    .values("count")[:1]
                ),
            }
        )
    return queryset


def annotate_with_matching_reviews(
    qs,
    match_review_on,
    match_section_on,
    most_recent=False,
    fields=None,
    prefix="",
    extra_metrics=True,
):
    """
    Annotate each element the passed-in queryset with a subset of all review averages.
    :param qs: queryset to annotate.
    :param match_review_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param: match_section_on: `Q()` expression representing a filtered subset of sections to group
        for each row. This should essentially be the same as match_review_on, but translated
        to Section filters. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param most_recent: If `True`, only aggregate results for the most recent semester.
    :param fields: list of fields to aggregate.
    :param prefix: prefix of annotated fields on the queryset.
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment,
        percent of add/drop period open, average number of openings during add/drop,
        and percentage of sections filled in advance registration
    """

    from courses.models import Section  # avoid circular imports

    if fields is None:
        fields = ALL_FIELD_SLUGS

    matching_reviews = Review.objects.filter(match_review_on, responses__gt=0)
    reviewbit_subfilters = Q(review_id__in=Subquery(matching_reviews.values("id")))
    matching_sections = Section.objects.filter(match_section_on)
    section_subfilters = Q(id__in=Subquery(matching_sections.values("id")))
    if most_recent:
        # Filter the queryset to include only rows from the most recent semester.
        recent_sem_subquery = Subquery(
            matching_reviews.annotate(common=Value(1))
            .values("common")
            .annotate(max_semester=Max("section__course__semester"))
            .values("max_semester")[:1]
        )
        reviewbit_subfilters &= Q(review__section__course__semester=recent_sem_subquery)
        section_subfilters &= Q(course__semester=recent_sem_subquery)

    return review_averages(
        qs,
        reviewbit_subfilters,
        section_subfilters,
        fields,
        prefix,
        semester_aggregations=True,
        extra_metrics=extra_metrics,
    )


def annotate_average_and_recent(
    qs, match_review_on, match_section_on, extra_metrics=True, fields=None
):
    """
    Annotate queryset with both all reviews and recent reviews.
    :param qs: Queryset to annotate.
    :param match_review_on: `Q()` expression representing a filtered subset of reviews to aggregate
        for each row. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param: match_section_on: `Q()` expression representing a filtered subset of sections to group
        for each row. This should essentially be the same as match_review_on, but translated
        to Section filters. Use `OuterRef(OuterRef('<field>'))` to refer to <field> on the row
        in the queryset.
    :param: extra_metrics: option to include extra metrics in PCR aggregations; final enrollment,
        percent of add/drop period open, average number of openings during add/drop,
        and percentage of sections filled in advance registration
    :param: fields: option to specify the fields averaged by the query
    """
    qs = annotate_with_matching_reviews(
        qs,
        match_review_on,
        match_section_on,
        most_recent=False,
        prefix="average_",
        extra_metrics=extra_metrics,
        fields=fields,
    )
    qs = annotate_with_matching_reviews(
        qs,
        match_review_on,
        match_section_on,
        most_recent=True,
        prefix="recent_",
        extra_metrics=extra_metrics,
        fields=fields,
    )
    return qs
