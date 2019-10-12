from django.db.models import Q

from courses.models import Requirement
from courses.views import CourseDetail, CourseList

from .search import TypedSearchBackend
from .serializers import CourseDetailWithReviewSerializer, CourseListWithReviewSerializer


class CourseListSearch(CourseList):
    filter_backends = (TypedSearchBackend, )
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    serializer_class = CourseListWithReviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        req_ids = self.request.query_params.get('requirements')
        if req_ids is not None:
            query = Q()
            for req_id in req_ids.split(','):
                code, school = req_id.split('@')
                try:
                    requirement = Requirement.objects.get(semester=self.get_semester(), code=code, school=school)
                except Requirement.DoesNotExist:
                    continue
                query |= Q(id__in=requirement.satisfying_courses.all())
            queryset = queryset.filter(query)

        return queryset


class CourseDetailSearch(CourseDetail):
    serializer_class = CourseDetailWithReviewSerializer
