from django.db import IntegrityError
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.util import get_course_and_section
from courses.views import CourseList
from options.models import get_value
from plan.filters import bound_filter, requirement_filter
from plan.models import Schedule
from plan.search import TypedSearchBackend
from plan.serializers import ScheduleSerializer


class CourseListSearch(CourseList):
    filter_backends = [TypedSearchBackend]
    search_fields = ('full_code', 'title', 'sections__instructors__name')

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(Prefetch('sections'))

        filters = {
            'requirements': requirement_filter,
            'cu': bound_filter('sections__credits'),
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
    sections = None
    if 'meetings' in data:
        sections = []
        for s in data.get('meetings'):
            _, section = get_course_and_section(s.get('id'), s.get('semester'))
            sections.append(section)
    elif 'sections' in data:
        sections = []
        for s in data.get('sections'):
            _, section = get_course_and_section(s.get('id'), s.get('semester'))
            sections.append(section)
    return sections


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        try:
            schedule = Schedule.objects.get(id=pk)
        except Schedule.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if 'semester' not in request.data:
            request.data['semester'] = get_value('SEMESTER', None)

        for s in request.data['sections']:
            if s.get('semester') != request.data.get('semester'):
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
        if Schedule.objects.filter(id=request.data.get('id')).exists():
            return self.update(request, request.data.get('id'))

        if 'semester' not in request.data:
            request.data['semester'] = get_value('SEMESTER', None)

        for sec in request.data['sections']:
            if sec.get('semester') != request.data.get('semester'):
                return Response({'detail': 'Semester uniformity invariant violated.'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            if 'id' in request.data:  # Also from above we know that this id does not conflict with existing schedules.
                schedule = Schedule.objects.create(person=request.user,
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
        queryset = super().get_serializer_class().setup_eager_loading(queryset)
        return queryset
