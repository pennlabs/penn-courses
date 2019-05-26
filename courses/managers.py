from django.db import models
from django.db.models import Avg, Subquery, OuterRef

from review.models import ReviewBit


class CourseManager(models.Manager):
    fields = ['course_quality', 'difficulty', 'instructor_quality']

    def get_queryset(self):
        return super().get_queryset().annotate(**{
            field: Subquery(
                ReviewBit.objects.filter(review__section__course__full_code=OuterRef('full_code'),
                                         field=field)
                .values('field')
                .order_by()
                .annotate(avg=Avg('score'))
                .values('avg')[:1]

            )
            for field in self.fields
        })


class SectionManager(models.Manager):
    fields = ['course_quality', 'difficulty', 'instructor_quality']

    def get_queryset(self):
        return super().get_queryset().annotate(**{
            field: Subquery(
                ReviewBit.objects.filter(review__section__course__full_code=OuterRef('course__full_code'),
                                         review__instructor__in=OuterRef('instructors'),
                                         field=field)
                .values('field')
                .order_by()
                .annotate(avg=Avg('score'))
                .values('avg')[:1],
                output_field=models.FloatField())
            for field in self.fields
        })
