from rest_framework import serializers
from .models import *


class MeetingSerializer(serializers.ModelSerializer):
    room = serializers.StringRelatedField()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('room',
                                             'room__building')
        return queryset

    class Meta:
        model = Meeting
        fields = (
            'day',
            'start',
            'end',
            'room'
        )


class SectionIdField(serializers.RelatedField):
    def to_representation(self, value):
        return {
            'id': value.normalized,
            'activity': value.activity
        }


class SectionSerializer(serializers.ModelSerializer):
    section_id = serializers.ReadOnlyField(source='normalized')
    semester = serializers.SerializerMethodField()
    meetings = MeetingSerializer(many=True)

    @staticmethod
    def get_semester(obj):
        return obj.course.semester

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('course__department',
                                             'meetings__room__building',
                                             'associated_sections__course__department')
        return queryset

    class Meta:
        model = Section
        fields = [
            'section_id',
            'status',
            'activity',
            'credits',
            'semester',
            'meetings',
        ]


class SectionDetailSerializer(SectionSerializer):
    associated_sections = SectionIdField(many=True, read_only=True)

    class Meta:
        model = Section
        fields = [
            'section_id',
            'status',
            'activity',
            'credits',
            'semester',
            'meetings',
        ] + [
            'associated_sections',
            'prereq_notes',
        ]


class CourseIdField(serializers.RelatedField):
    def to_representation(self, value):
        return value.course_id


class CourseListSerializer(serializers.ModelSerializer):
    course_id = serializers.ReadOnlyField()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department')
        return queryset

    class Meta:
        model = Course
        fields = [
            'course_id',
            'title',
            'description',
            'semester',
        ]


class CourseDetailSerializer(CourseListSerializer):
    crosslistings = CourseIdField(many=True, read_only=True)
    sections = SectionDetailSerializer(many=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             'sections__course__department',
                                             'sections__meetings__room__building',
                                             'sections__associated_sections__course__department',
                                             'sections__associated_sections__meetings__room__building')
        return queryset

    class Meta:
        model = Course
        fields = [
            'course_id',
            'title',
            'description',
            'semester',
        ] + [
            'crosslistings',
            'sections',
        ]
