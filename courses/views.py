from django.shortcuts import render

from rest_framework import mixins
from rest_framework import generics

from .serializers import *
from .models import *


class SectionList(mixins.ListModelMixin,
                  generics.GenericAPIView):

    serializer_class = SectionSerializer

    def get_queryset(self):
        queryset = Section.objects.all()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)