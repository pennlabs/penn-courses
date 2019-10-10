from django.db.models import Q

from courses.models import Requirement
from courses.views import CourseDetail, CourseList

from .search import TypedSearchBackend
from .serializers import CourseDetailWithReviewSerializer, CourseListWithReviewSerializer
from .filters import requirement_filter


class CourseListSearch(CourseList):
    filter_backends = [TypedSearchBackend]
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    serializer_class = CourseListWithReviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        req_ids = self.request.query_params.get('requirements')
        if req_ids is not None:
            queryset = requirement_filter(queryset, req_ids, self.get_semester())

        return queryset


class CourseDetailSearch(CourseDetail):
    serializer_class = CourseDetailWithReviewSerializer
