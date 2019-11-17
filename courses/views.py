from rest_framework import filters, generics, viewsets
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from courses.models import Course, Requirement, Section, UserData
from courses.serializers import (CourseDetailSerializer, CourseListSerializer, MiniSectionSerializer,
                                 RequirementListSerializer, UserDataSerializer)
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
    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['^full_code']

    @staticmethod
    def get_semester_field():
        return 'course__semester'


class CourseList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = CourseListSerializer
    queryset = Course.with_reviews.filter(sections__isnull=False)


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    serializer_class = CourseDetailSerializer
    lookup_field = 'full_code'
    queryset = Course.with_reviews.all()


class RequirementList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = RequirementListSerializer
    queryset = Requirement.objects.all()


class UserDetailView(generics.RetrieveAPIView, generics.UpdateAPIView):
    serializer_class = UserDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserData.objects.all()

    def get_object(self):
        return self.request.user
