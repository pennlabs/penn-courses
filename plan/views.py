from django.db import IntegrityError
from django.db.models import Prefetch
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Section
from courses.util import get_or_create_course_and_section
from courses.views import CourseList
from options.models import get_value
from plan.filters import bound_filter, choice_filter, requirement_filter
from plan.models import Schedule
from plan.search import TypedCourseSearchBackend
from plan.serializers import ScheduleSerializer


class CourseListSearch(CourseList):
    filter_backends = [TypedCourseSearchBackend]
    search_fields = ('full_code', 'title', 'sections__instructors__name')

    def get_queryset(self):
        queryset = super().get_queryset()

        filters = {
            'requirements': requirement_filter,
            'cu': choice_filter('sections__credits'),
            'activity': choice_filter('sections__activity'),
            'course_quality': bound_filter('course_quality'),
            'instructor_quality': bound_filter('instructor_quality'),
            'difficulty': bound_filter('difficulty')
        }

        for field, filter_func in filters.items():
            param = self.request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param, self.get_semester())

        return queryset.distinct()


def get_sections(data):
    raw_sections = []
    if 'meetings' in data:
        raw_sections = data.get('meetings')
    elif 'sections' in data:
        raw_sections = data.get('sections')
    else:
        return None
    sections = []
    for s in raw_sections:
        _, section = get_or_create_course_and_section(s.get('id'),
                                                      s.get('semester'))
        sections.append(section)
    return sections


class ScheduleViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        try:
            schedule = self.get_queryset().get(id=pk)
        except Schedule.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if 'semester' not in request.data:
            request.data['semester'] = get_value('SEMESTER', None)

        sections = get_sections(request.data)

        for s in sections:
            if s.course.semester != request.data.get('semester'):
                return Response({'detail': 'Semester uniformity invariant violated.'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            schedule.person = request.user
            schedule.semester = request.data.get('semester')
            schedule.name = request.data.get('name')
            schedule.save()
            schedule.sections.set(get_sections(request.data))
            serialized_schedule = ScheduleSerializer(schedule)
            return Response(serialized_schedule.data, status=status.HTTP_202_ACCEPTED)
        except IntegrityError as e:
            return Response({'detail': 'Probably unique constraint violated... error: ' + str(e.__cause__)},
                            status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        if self.get_queryset().filter(id=request.data.get('id')).exists():
            return self.update(request, request.data.get('id'))

        if 'semester' not in request.data:
            request.data['semester'] = get_value('SEMESTER', None)

        sections = get_sections(request.data)

        for sec in sections:
            if sec.course.semester != request.data.get('semester'):
                return Response({'detail': 'Semester uniformity invariant violated.'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            if 'id' in request.data:  # Also from above we know that this id does not conflict with existing schedules.
                schedule = self.get_queryset().create(person=request.user,
                                                      semester=request.data.get('semester'),
                                                      name=request.data.get('name'),
                                                      id=request.data.get('id'))
            else:
                schedule = Schedule.objects.create(person=request.user,
                                                   semester=request.data.get('semester'),
                                                   name=request.data.get('name'))
            schedule.sections.set(get_sections(request.data))
            serialized_schedule = ScheduleSerializer(schedule)
            return Response(serialized_schedule.data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            return Response({'detail': 'Probably unique constraint violated... error: ' + str(e.__cause__)},
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Schedule.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            Prefetch('sections', Section.with_reviews.all()),
        )
        return queryset
