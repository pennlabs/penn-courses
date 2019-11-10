from django.db.models import Avg, FloatField, OuterRef, Subquery

from review.models import ReviewBit


"""
Queryset annotations
====================

This file has code which annotates Course and Section querysets with Review information.
There's some tricky JOINs going on here, through the Subquery objects which you can read about here:
https://docs.djangoproject.com/en/2.2/ref/models/expressions/#subquery-expressions.

This allows us to have the database do all of the work of averaging PCR data, so that we can get all of our Course and
Section data in two queries.
"""


# Annotations are basically the same for Course and Section, save a few of the subfilters, so generalize it out.
def review_averages(queryset, subfilters):
    fields = ['course_quality', 'difficulty', 'instructor_quality', 'work_required']
    return queryset.annotate(**{
        field: Subquery(
            ReviewBit.objects.filter(field=field, **subfilters)
            .values('field')
            .order_by()
            .annotate(avg=Avg('score'))
            .values('avg')[:1],
            output_field=FloatField())
        for field in fields
    })


def sections_with_reviews(queryset):
    return review_averages(
        queryset,
        {
            'review__section__course__full_code': OuterRef('course__full_code'),
            'review__instructor__in': OuterRef('instructors')
        }
    ).order_by('code')


def course_reviews(queryset):
    return review_averages(queryset, {'review__section__course__full_code': OuterRef('full_code')})
