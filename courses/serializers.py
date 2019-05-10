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
    associated_sections = SectionIdField(many=True, read_only=True)

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
        fields = (
            'section_id',
            'activity',
            'credits',
            'semester',
            'meetings',
            'associated_sections',
        )