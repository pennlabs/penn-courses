from django.shortcuts import render

from courses.views import CourseList
from .search import TypedSearchBackend

from courses.models import Requirement


class CourseListSearch(CourseList):
    filter_backends = (TypedSearchBackend, )
    search_fields = ('full_code', 'title', 'sections__instructors__name')

    def get_queryset(self):
        queryset = super().get_queryset()

        req_id = self.request.query_params.get('requirement')
        if req_id is not None:
            code, school = req_id.split('@')
            try:
                requirement = Requirement.objects.get(semester=self.get_semester(), code=code, school=school)
            except Requirement.DoesNotExist:
                return queryset.none()
            queryset = queryset.filter(id__in=requirement.satisfying_courses.all())

        return queryset
