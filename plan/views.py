from django.db.models import Prefetch

from courses.views import CourseDetail, CourseList
from plan.filters import bound_filter, requirement_filter
from plan.search import TypedSearchBackend
from plan.serializers import CourseDetailWithReviewSerializer, CourseListWithReviewSerializer


class CourseListSearch(CourseList):
    filter_backends = [TypedSearchBackend]
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    serializer_class = CourseListWithReviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(Prefetch('sections'))

        filters = {
            'requirements': requirement_filter,
            'cu': bound_filter('sections__credits'),
            'course_quality': bound_filter('course_quality'),
            'instructor_quality': bound_filter('instructor_quality'),
            'difficulty': bound_filter('difficulty')
        }

        for field, filter_func in filters.items():
            param = self.request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param, self.get_semester())

        return queryset.distinct()


class CourseDetailSearch(CourseDetail):
    serializer_class = CourseDetailWithReviewSerializer
