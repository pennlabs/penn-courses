from django.shortcuts import render

from rest_framework import mixins, generics, filters

from .serializers import *
from .models import *


class SectionList(generics.ListAPIView):

    serializer_class = SectionSerializer

    def get_queryset(self):
        queryset = Section.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class CourseList(generics.ListAPIView):
    serializer_class = CourseListSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('department__code', )

    def get_queryset(self):
        queryset = Course.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset


class CourseDetail(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer

    def get_queryset(self):
        queryset = Course.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset
