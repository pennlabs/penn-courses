from rest_framework import serializers

from courses.serializers import CourseListSerializer, SectionDetailSerializer
from courses.models import Course


class CourseListSearchSerializer(CourseListSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)

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
