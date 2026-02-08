from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery, Avg, F, Value, IntegerField

from courses.models import Course, Section, Instructor
from review.models import ReviewBit, Review
from review.views import section_filters_pcr


def calculate_course_review_averages(course_queryset, stdout):
    """
    Calculates and updates review averages for a given Course queryset.
    """
    # Use a simplified version of review_averages that only focuses on Course data
    # We need to re-implement some parts as review_averages is too generic for direct use here
    annotated_queryset = course_queryset.annotate(
        avg_course_quality=Subquery(
            ReviewBit.objects.filter(
                review__section__course__topic=OuterRef('topic'),
                field='course_quality',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_instructor_quality=Subquery(
            ReviewBit.objects.filter(
                review__section__course__topic=OuterRef('topic'),
                field='instructor_quality',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_difficulty=Subquery(
            ReviewBit.objects.filter(
                review__section__course__topic=OuterRef('topic'),
                field='difficulty',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_work_required=Subquery(
            ReviewBit.objects.filter(
                review__section__course__topic=OuterRef('topic'),
                field='work_required',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
    )

    with transaction.atomic():
        for course in tqdm(annotated_queryset, desc="Updating Course Averages", file=stdout):
            Course.objects.filter(pk=course.pk).update(
                course_quality=course.avg_course_quality,
                instructor_quality=course.avg_instructor_quality,
                difficulty=course.avg_difficulty,
                work_required=course.avg_work_required,
            )

def calculate_section_review_averages(section_queryset, stdout):
    """
    Calculates and updates review averages for a given Section queryset.
    """
    # Similar to calculate_course_review_averages, we need to re-implement for sections
    # as the original review_averages was too generic.

    # Subquery for instructors related to the section
    instructors_subquery = Subquery(
        Instructor.objects.filter(section__id=OuterRef(OuterRef("id"))).values("id")
    )

    annotated_queryset = section_queryset.annotate(
        avg_course_quality=Subquery(
            ReviewBit.objects.filter(
                Q(review__section__course__topic=OuterRef('course__topic')) & \
                Q(review__instructor__in=instructors_subquery),
                field='course_quality',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_instructor_quality=Subquery(
            ReviewBit.objects.filter(
                Q(review__section__course__topic=OuterRef('course__topic')) & \
                Q(review__instructor__in=instructors_subquery),
                field='instructor_quality',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_difficulty=Subquery(
            ReviewBit.objects.filter(
                Q(review__section__course__topic=OuterRef('course__topic')) & \
                Q(review__instructor__in=instructors_subquery),
                field='difficulty',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
        avg_work_required=Subquery(
            ReviewBit.objects.filter(
                Q(review__section__course__topic=OuterRef('course__topic')) & \
                Q(review__instructor__in=instructors_subquery),
                field='work_required',
                review__responses__gt=0,
            )
            .values('field')
            .order_by()
            .annotate(avg=Avg('average'))
            .values('avg')[:1]
        ),
    )

    with transaction.atomic():
        for section in tqdm(annotated_queryset, desc="Updating Section Averages", file=stdout):
            Section.objects.filter(pk=section.pk).update(
                course_quality=section.avg_course_quality,
                instructor_quality=section.avg_instructor_quality,
                difficulty=section.avg_difficulty,
                work_required=section.avg_work_required,
            )


class Command(BaseCommand):
    help = 'Calculates and saves review averages for Course and Section models.'

    def handle(self, *args, **options):
        self.stdout.write("Calculating Course review averages...")
        calculate_course_review_averages(Course.objects.all(), self.stdout)
        self.stdout.write(self.style.SUCCESS("Finished calculating Course review averages."))

        self.stdout.write("Calculating Section review averages...")
        calculate_section_review_averages(Section.objects.all(), self.stdout)
        self.stdout.write(self.style.SUCCESS("Finished calculating Section review averages."))
