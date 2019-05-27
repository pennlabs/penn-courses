from rest_framework import serializers
from django.db.models import Prefetch, OuterRef

from courses.serializers import CourseListSerializer, CourseDetailSerializer, SectionDetailSerializer
from courses.models import Course, Section
from plan import annotations


class CourseListSearchSerializer(CourseListSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = annotations.review_averages(queryset, {'review__section__course__full_code': OuterRef('full_code')})
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             'sections__review_set__reviewbit_set'
                                             )
        return queryset

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'semester',
            'course_quality',
            'instructor_quality',
            'difficulty'
        ]


class SectionDetailPlanSerializer(SectionDetailSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)

    class Meta:
        model = Section
        fields = [
            'id',
            'status',
            'activity',
            'credits',
            'semester',
            'course_quality',
            'instructor_quality',
            'difficulty',
            'meetings',
        ] + [
            'associated_sections',
            'prereq_notes',
        ]


class CourseDetailPlanSerializer(CourseDetailSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)

    sections = SectionDetailPlanSerializer(many=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            Prefetch('sections', queryset=annotations.sections_with_reviews()),
            'primary_listing__listing_set__department',
            'department',
            'sections__course__department',
            'sections__meetings__room__building',
            'sections__associated_sections__course__department',
            'sections__associated_sections__meetings__room__building',
            'department__requirements',
            'requirement_set',
            'nonrequirement_set')
        return queryset

    class Meta:
        model = Course
        fields = [
             'id',
             'title',
             'description',
             'semester',
             'course_quality',
             'instructor_quality',
             'difficulty'
         ] + [
             'crosslistings',
             'requirements',
             'sections',
         ]
