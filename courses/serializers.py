from rest_framework import serializers

from courses.models import Course, Meeting, Requirement, Section


class MeetingSerializer(serializers.ModelSerializer):
    room = serializers.StringRelatedField()

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
            'id': value.full_code,
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


class SectionDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='full_code')
    semester = serializers.SerializerMethodField()
    meetings = MeetingSerializer(many=True)
    instructors = serializers.StringRelatedField(many=True)
    associated_sections = SectionIdField(many=True, read_only=True)

    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    @staticmethod
    def get_semester(obj):
        return obj.course.semester

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
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required'
        ] + [
            'associated_sections',
        ]


class RequirementListSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

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


class CourseListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='full_code')
    num_sections = serializers.SerializerMethodField()

    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    def get_num_sections(self, obj):
        return obj.sections.count()

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'semester',
            'num_sections',
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
        ]


class CourseDetailSerializer(CourseListSerializer):
    crosslistings = serializers.SlugRelatedField(slug_field='full_code', many=True, read_only=True)
    sections = SectionDetailSerializer(many=True)
    requirements = RequirementListSerializer(many=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'semester',
            'prerequisites',
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
        ] + [
            'crosslistings',
            'requirements',
            'sections',
        ]
