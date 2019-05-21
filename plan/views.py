from django.shortcuts import render

from courses.views import CourseList
from .search import TypedSearchBackend


class CourseListSearch(CourseList):
    filter_backends = (TypedSearchBackend, )
    search_fields = ('full_code', 'title', 'sections__instructors__name')

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
