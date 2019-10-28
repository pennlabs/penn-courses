from django.http import HttpResponse
from rest_framework import generics

from courses.models import Course, Requirement
from courses.serializers import CourseDetailSerializer, CourseListSerializer, RequirementListSerializer
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


class CourseList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = CourseListSerializer
    queryset = Course.objects.filter(sections__isnull=False)


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    serializer_class = CourseDetailSerializer
    lookup_field = 'full_code'
    queryset = Course.objects.all()


class RequirementList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = RequirementListSerializer
    queryset = Requirement.objects.all()


def index(request):
    return HttpResponse(f'Hello, {request.site}')
