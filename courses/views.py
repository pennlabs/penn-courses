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
    def get_search_fields(self, view, request):
        search_type = request.GET.get('type')

        if search_type == 'dept':
            return ['department__code']
        elif search_type == 'course':
            return ['full_code']
        elif search_type == 'keyword':
            return ['title', 'sections__instructors__name']
        else:
            return getattr(view, 'search_fields', None)


class CourseList(generics.ListAPIView):
    serializer_class = CourseListSerializer
    filter_backends = (TypedSearchBackend,)
    search_fields = ('department__code', 'code', 'title', 'sections__instructors__name')

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
