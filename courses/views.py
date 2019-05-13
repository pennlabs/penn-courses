import re

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import mixins, generics, filters

from .serializers import *
from .models import *


class SectionList(generics.ListAPIView):
    serializer_class = SectionSerializer

    def get_queryset(self):
        queryset = Section.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class TypedSearchBackend(filters.SearchFilter):
    code_re = re.compile(r'^([A-Za-z]{1,4})?[ |-]?(\d{1,5})?$')

    def infer_search_type(self, query):
        if self.code_re.match(query):
            return 'course'
        else:
            return 'keyword'

    def get_search_terms(self, request):
        term = request.query_params.get(self.search_param, '')
        match = self.code_re.match(term)
        if match and match.group(1) and match.group(2):
            term = f'{match.group(1)}-{match.group(2)}'
        return [term]

    def get_search_fields(self, view, request):
        search_type = request.GET.get('type')

        if search_type == 'auto':
            search_type = self.infer_search_type(request.GET.get('search'))

        if search_type == 'course':
            return ['full_code']
        elif search_type == 'keyword':
            return ['title', 'sections__instructors__name']
        else:
            return super().get_search_fields(view, request)


class CourseList(generics.ListAPIView):
    serializer_class = CourseListSerializer
    filter_backends = (TypedSearchBackend,)
    search_fields = ('full_code', 'title', 'sections__instructors__name')

    def get_queryset(self):
        queryset = Course.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset


class CourseDetail(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    lookup_field = 'full_code'

    def get_queryset(self):
        queryset = Course.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


def index(request):
    return HttpResponse(f'Hello, {request.site}')
