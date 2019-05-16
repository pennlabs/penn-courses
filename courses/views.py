import re

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import mixins, generics, filters

from options.models import get_value

from .serializers import *
from .models import *


class TypedSearchBackend(filters.SearchFilter):
    code_re = re.compile(r'^([A-Za-z]{1,4})?[ |-]?(\d{1,5})?$')

    def infer_search_type(self, query):
        if self.code_re.match(query):
            return 'course'
        else:
            return 'keyword'

    @staticmethod
    def get_search_type(request):
        return request.GET.get('type')

    def get_search_terms(self, request):
        search_type = self.get_search_type(request)
        query = request.query_params.get(self.search_param, '')

        match = self.code_re.match(query)
        # If this is a course query, either by designation or by detection,
        if (search_type == 'course' or (search_type == 'auto' and self.infer_search_type(query) == 'course')) \
                and match and match.group(1) and match.group(2):
            query = f'{match.group(1)}-{match.group(2)}'
        return [query]

    def get_search_fields(self, view, request):
        search_type = self.get_search_type(request)

        if search_type == 'auto':
            search_type = self.infer_search_type(request.GET.get('search'))

        if search_type == 'course':
            return ['full_code']
        elif search_type == 'keyword':
            return ['title', 'sections__instructors__name']
        else:
            return super().get_search_fields(view, request)


class BaseCourseMixin(generics.GenericAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        semester = self.kwargs.get('semester', 'all')
        if semester == 'current':
            semester = get_value('SEMESTER', 'all')

        if semester != 'all':
            queryset = queryset.filter(semester=semester)
        return queryset


class SectionList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = SectionSerializer
    queryset = Section.objects.all()


class CourseList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = CourseListSerializer
    filter_backends = (TypedSearchBackend,)
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    queryset = Course.objects.all()


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    serializer_class = CourseDetailSerializer
    lookup_field = 'full_code'
    queryset = Course.objects.all()


def index(request):
    return HttpResponse(f'Hello, {request.site}')
