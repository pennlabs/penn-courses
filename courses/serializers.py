from django.db.models import Prefetch, Q
from rest_framework import serializers

from courses.models import Course, Meeting, Requirement, Section


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


class MiniSectionSerializer(serializers.ModelSerializer):
    section_id = serializers.CharField(source='full_code')
    instructors = serializers.StringRelatedField(many=True)
    course_title = serializers.SerializerMethodField()

    def get_course_title(self, obj):
        return obj.course.title

    class Meta:
        model = Section
        fields = [
            'section_id',
            'status',
            'activity',
            'meeting_times',
            'instructors',
            'course_title',
        ]

    @staticmethod
    def get_semester(obj):
        return obj.course.semester

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('course', 'course__department', 'instructors')
        return queryset


class SectionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='full_code')
    semester = serializers.SerializerMethodField()
    meetings = MeetingSerializer(many=True)
    instructors = serializers.StringRelatedField(many=True)

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
            'id',
            'status',
            'activity',
            'credits',
            'semester',
            'meetings',
            'instructors',
        ]


class SectionDetailSerializer(SectionSerializer):
    associated_sections = SectionIdField(many=True, read_only=True)

    class Meta:
        model = Section
        fields = [
            'id',
            'status',
            'activity',
            'credits',
            'semester',
            'meetings',
            'instructors',
        ] + [
            'associated_sections',
        ]


class CourseIdField(serializers.RelatedField):
    def to_representation(self, value):
        return value.course_id


class RequirementListSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    @staticmethod
    def setup_eager_loading(queryset):
        return queryset

    @staticmethod
    def get_id(obj):
        return f'{obj.code}@{obj.school}'

    class Meta:
        model = Requirement
        fields = [
            'id',
            'code',
            'school',
            'semester',
            'name'
        ]


class RequirementDetailSerializer(RequirementListSerializer):
    satisfying_courses = CourseIdField(many=True, read_only=True)

    class Meta:
        model = Requirement
        fields = [
            'code',
            'school',
            'semester',
            'name'
        ] + [
            'satisfying_courses'
        ]


class CourseListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='course_id')
    num_sections = serializers.SerializerMethodField()

    def get_num_sections(self, obj):
        return obj.sections.count()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             Prefetch('sections',
                                                      Section.objects
                                                      .filter(meetings__isnull=False)
                                                      .filter(credits__isnull=False)
                                                      .filter(Q(status='O') | Q(status='C')).distinct()),
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
            'num_sections',
        ]


class CourseDetailSerializer(CourseListSerializer):
    crosslistings = CourseIdField(many=True, read_only=True)
    sections = SectionDetailSerializer(many=True)
    requirements = RequirementListSerializer(many=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             Prefetch('sections',
                                                      Section.objects
                                                      .filter(meetings__isnull=False)
                                                      .filter(credits__isnull=False)
                                                      .filter(Q(status='O') | Q(status='C')).distinct()),
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
        ] + [
            'crosslistings',
            'requirements',
            'sections',
        ]
