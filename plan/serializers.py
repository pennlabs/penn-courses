from django.db.models import Manager, OuterRef, Prefetch, Q
from rest_framework import serializers

from courses.models import Course, Section
from courses.serializers import CourseDetailSerializer, CourseListSerializer, SectionDetailSerializer
from plan import annotations


def unique(lst):
    previous = float('NaN')
    result = []
    for elt in lst:
        if elt != previous:
            result.append(elt)
        previous = elt
    return result


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


class CourseListWithReviewSerializer(CourseListSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    @staticmethod
    def setup_eager_loading(queryset):
        # annotate the queryset with course review averages before prefetching related models.
        queryset = annotations.review_averages(queryset, {'review__section__course__full_code': OuterRef('full_code')})
        queryset = queryset.prefetch_related('primary_listing__listing_set__department',
                                             'department',
                                             Prefetch('sections',
                                                      queryset=annotations.sections_with_reviews()
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
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
            'num_sections',
        ]


class SectionDetailWithReviewSerializer(SectionDetailSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = annotations.sections_with_reviews()
        queryset = queryset.prefetch_related(
            'course__department',
            'meetings__room__building',
            'associated_sections__course__department',
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
            'course_quality',
            'instructor_quality',
            'difficulty',
            'work_required',
            'meetings',
            'instructors',
        ] + [
            'associated_sections',
        ]


class CourseDetailWithReviewSerializer(CourseDetailSerializer):
    course_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    difficulty = serializers.DecimalField(max_digits=4, decimal_places=3)
    instructor_quality = serializers.DecimalField(max_digits=4, decimal_places=3)
    work_required = serializers.DecimalField(max_digits=4, decimal_places=3)

    sections = SectionDetailWithReviewSerializer(many=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = annotations.review_averages(queryset, {'review__section__course__full_code': OuterRef('full_code')})
        queryset = queryset.prefetch_related(
            # prefetch sections using the annotated queryset, so we get review averages along with the sections.
            Prefetch('sections',
                     queryset=annotations.sections_with_reviews()
                     .filter(meetings__isnull=False)
                     .filter(credits__isnull=False)
                     .filter(Q(status='O') | Q(status='C')).distinct()),
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
             'difficulty',
             'work_required',
         ] + [
             'crosslistings',
             'requirements',
             'sections',
         ]
