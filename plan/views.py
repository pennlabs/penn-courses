from django.db import IntegrityError
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.util import get_course_and_section
from courses.views import CourseDetail, CourseList
from plan.filters import bound_filter, requirement_filter
from plan.models import Schedule
from plan.search import TypedSearchBackend
from plan.serializers import CourseDetailWithReviewSerializer, CourseListWithReviewSerializer, ScheduleSerializer


class CourseListSearch(CourseList):
    filter_backends = [TypedSearchBackend]
    search_fields = ('full_code', 'title', 'sections__instructors__name')
    serializer_class = CourseListWithReviewSerializer

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


class CourseDetailSearch(CourseDetail):
    serializer_class = CourseDetailWithReviewSerializer


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
        existing_obs = Schedule.objects.filter(id=pk)
        if (len(existing_obs) == 0):
            return Response({'detail': 'No schedule with key: '+pk+' exists.'}, status=status.HTTP_400_BAD_REQUEST)

        for s in request.data['sections']:
            if s['semester'] != request.data['semester']:
                return Response({'detail': 'Semester uniformity invariant violated.'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_obs.update(person=request.user,
                                semester=request.data.get('semester'),
                                name=request.data.get('name'),
                                )
            ob = existing_obs[0]
            ob.sections.set(get_sections(request.data))
            s = ScheduleSerializer(ob)
            return Response(s.data, status=status.HTTP_202_ACCEPTED)
        except IntegrityError:
            return Response({'detail': 'Unique constraint violated'}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        existing_obs = Schedule.objects.filter(id=request.data.get('id'))
        if len(existing_obs) > 0:
            return self.update(request, request.data.get('id'))

        for s in request.data['sections']:
            if s['semester'] != request.data['semester']:
                return Response({'detail': 'Semester uniformity invariant violated.'},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            if request.data.get('id'):
                ob = Schedule.objects.create(person=request.user,
                                             semester=request.data.get('semester'),
                                             name=request.data.get('name'),
                                             id=request.data.get('id'))
            else:
                ob = Schedule.objects.create(person=request.user,
                                             semester=request.data.get('semester'),
                                             name=request.data.get('name'))
            ob.sections.set(get_sections(request.data))
            s = ScheduleSerializer(ob)
            return Response(s.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'detail': 'Unique constraint violated'}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Schedule.objects.filter(person=self.request.user)
        queryset = super().get_serializer_class().setup_eager_loading(queryset)
        return queryset
