from django.http import HttpResponse
from rest_framework import generics

from .serializers import *
from .models import *

from options.models import get_value


class BaseCourseMixin(generics.GenericAPIView):
    @staticmethod
    def get_semester_field():
        return 'semester'

    def get_semester(self):
        semester = self.kwargs.get('semester', 'current')
        if semester == 'current':
            semester = get_value('SEMESTER', 'all')

        return semester

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        # if we're in a view without a semester parameter, only return the current semester.
        semester = self.get_semester()
        if semester != 'all':
            queryset = queryset.filter(**{self.get_semester_field(): semester})
        return queryset


class SectionList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = SectionSerializer
    queryset = Section.objects.all()

    @staticmethod
    def get_semester_field():
        return 'course__semester'


class CourseList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = CourseListSerializer
    queryset = Course.objects.all()


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    serializer_class = CourseDetailSerializer
    lookup_field = 'full_code'
    queryset = Course.objects.all()


class RequirementList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = RequirementListSerializer
    queryset = Requirement.objects.all()


def index(request):
    return HttpResponse(f'Hello, {request.site}')
