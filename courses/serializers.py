from django.db.models import Manager, Prefetch, Q
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


"""
WARNING: This is most likely a hack. The review annotation seems to duplicate sections `m` times where `m` is the
number of instructors attached to a section. I'm guessing this has to do with the fact that Reviews are
per-instructor, so there's one row per review that's being aggregated. Any way, distinct() doesn't solve the issue
for some reason, and there's no DISTINCT ON operation in MySQL, so we need to solve the issue outside of SQL.
The solution which seems to impact effeciency the least is in the ListSerializer. Basically, right after
we evaluate the queryset and riht before we serialize each row, we remove duplicates with the python equivalent of the
`uniq` bash command. We know that this will hit all duplicates because the queryset is sorted by section ID,
so duplicates will be right next to each other.

TODO would be to find a way to do this in SQL, as it'll make the python code less complicated.
"""


def unique(lst):
    previous = float('NaN')
    result = []
    for elt in lst:
        if elt != previous:
            result.append(elt)
        previous = elt
    return result


class DeduplicateListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        # This method will take O(2mN) as opposed to O(mN) before, where N is number of sections in the set and m
        # is the maximum number of instructors on any section. Both numbers are generally constant anyways.
        iterable = data.all() if isinstance(data, Manager) else data
        iterable = unique(iterable)

        return [
            self.child.to_representation(item) for item in iterable
        ]

    def update(self, instance, validated_data):
        raise NotImplementedError(
            'Serializers with many=True do not support multiple update by '
            'default, only multiple create. For updates it is unclear how to '
            'deal with insertions and deletions. If you need to support '
            'multiple update, use a `ListSerializer` class and override '
            '`.update()` so you can specify the behavior exactly.'
        )


class SectionDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='normalized')
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

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('course__department',
                                             'meetings__room__building',
                                             'associated_sections__course__department',
                                             'associated_sections',
                                             )
        return queryset

    class Meta:
        model = Section
        list_serializer_class = DeduplicateListSerializer
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


class CourseListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='course_id')
    num_sections = serializers.SerializerMethodField()

    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    def get_num_sections(self, obj):
        return obj.sections.count()

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             Prefetch('sections',
                                                      Section.with_reviews.all()
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
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
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
                                                      Section.with_reviews.all()
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
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
        ] + [
            'crosslistings',
            'requirements',
            'sections',
        ]
