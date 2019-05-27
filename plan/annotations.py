from django.db.models import Subquery, OuterRef, Avg, FloatField

from review.models import ReviewBit
from courses.models import Section


def review_averages(queryset, subfilters):
    fields = ['course_quality', 'difficulty', 'instructor_quality']
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


def sections_with_reviews():
    return review_averages(
        Section.objects.all(),
        {
            'review__section__course__full_code': OuterRef('course__full_code'),
            'review__instructor__in': OuterRef('instructors')
        }
    )
