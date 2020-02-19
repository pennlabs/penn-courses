from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from django_auto_prefetching import AutoPrefetchViewSetMixin
from options.models import get_value
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Section
from courses.util import get_course_and_section
from courses.views import CourseList
from plan.filters import bound_filter, choice_filter, requirement_filter
from plan.models import Schedule
from plan.search import TypedCourseSearchBackend
from plan.serializers import ScheduleSerializer


class CourseListSearch(CourseList):
    """
    The main API endpoint for PCP. Without any GET parameters, it simply returns all courses for
    a given semester.

    The main API endpoint for PCP is the `/courses` endpoint. Without any `GET` parameters, it
    simply returns all courses for a given semester.

    - `search`

    The `search` parameter takes in the search query to subset the courses returned. By default,
    the search type is `auto`. (see below)

    - `type`

    There are three current options for `type`:

    - `auto` The default. Lets the backend decide which type of search to run.
    - `course` Search against a course's full code, which includes the department and course IDs:
    for example, `CIS120` should be a `course` query.
    - `keyword` Search against instructors names and words in the course's title. Both `Programming`
    and `Rajiv` are good `keyword` searches.

    ## Filters
    Filters are ANDed together.
    - `requirements`

    Filter search results by a given requirement, identified by `<code>@<school>`.
    For example, classes which fulfill the humanities requirement in Engineering could be filtered
    for with the requirement code `H@SEAS`. The same requirement at Wharton, which can include
    slightly different classes, can be accessed with `H@WH`. A full list of requirements with their
    IDs can be found with the `requirements/` endpoint described below.

    Filter by multiple requirements (OR'd together), separating ids by `,`. For example,
    `SS@SEAS,H@SEAS` will return all courses which match either social science or humanities
    requirements for SEAS students.

    ### Range Filters

    There are a few filters which constitute ranges of floating-point numbers. The values for these
    are `<min>-<max>` , with minimum excluded. For example, looking for classes in the range of
    0-2.5 in difficulty, you would add the parameter `difficulty=0-2.5`. Below are the list of range
    filters.

    - `cu` course units. Will match if any section of a course has course units which fall in that
    range.
    - `difficulty` course difficulty averaged from all reviews.
    - `course_quality` course quality averaged from all reviews.
    - `instructor_quality` instructor quality averaged from all reviews.
    """

    filter_backends = [TypedCourseSearchBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")

    def get_queryset(self):
        queryset = super().get_queryset()

        filters = {
            "requirements": requirement_filter,
            "cu": choice_filter("sections__credits"),
            "activity": choice_filter("sections__activity"),
            "course_quality": bound_filter("course_quality"),
            "instructor_quality": bound_filter("instructor_quality"),
            "difficulty": bound_filter("difficulty"),
        }

        for field, filter_func in filters.items():
            param = self.request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param, self.get_semester())

        return queryset.distinct()


class ScheduleViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    list:
    This route will return a list of schedules for the logged-in user, each with the fields
    detailed below.

    retrieve:
    Get a single schedule.

    """

    serializer_class = ScheduleSerializer
    http_method_names = ["get", "post", "delete", "put"]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_sections(data):
        raw_sections = []
        if "meetings" in data:
            raw_sections = data.get("meetings")
        elif "sections" in data:
            raw_sections = data.get("sections")
        sections = []
        for s in raw_sections:
            _, section = get_course_and_section(s.get("id"), s.get("semester"))
            sections.append(section)
        return sections

    @staticmethod
    def check_semester(data, sections):
        for i, s in enumerate(sections):
            if i == 0 and "semester" not in data:
                data["semester"] = s.course.semester
            elif s.course.semester != data.get("semester"):
                return Response(
                    {"detail": "Semester uniformity invariant violated."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if "semester" not in data:
            data["semester"] = get_value("SEMESTER", None)

    def update(self, request, pk=None):
        try:
            schedule = self.get_queryset().get(id=pk)
        except Schedule.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            sections = self.get_sections(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        semester_res = self.check_semester(request.data, sections)
        if semester_res is not None:
            return semester_res

        try:
            schedule.person = request.user
            schedule.semester = request.data.get("semester")
            schedule.name = request.data.get("name")
            schedule.save()
            schedule.sections.set(sections)
            return Response(
                {"message": "success", "id": schedule.id}, status=status.HTTP_202_ACCEPTED
            )
        except IntegrityError as e:
            return Response(
                {
                    "detail": "IntegrityError encountered while trying to update: "
                    + str(e.__cause__)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def create(self, request, *args, **kwargs):
        """
        - `title` - must be unique for a given user in this semester.
        - `meetings[*].semester` -
        """
        if self.get_queryset().filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))

        try:
            sections = self.get_sections(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        semester_res = self.check_semester(request.data, sections)
        if semester_res is not None:
            return semester_res

        try:
            if (
                "id" in request.data
            ):  # Also from above we know that this id does not conflict with existing schedules.
                schedule = self.get_queryset().create(
                    person=request.user,
                    semester=request.data.get("semester"),
                    name=request.data.get("name"),
                    id=request.data.get("id"),
                )
            else:
                schedule = self.get_queryset().create(
                    person=request.user,
                    semester=request.data.get("semester"),
                    name=request.data.get("name"),
                )
            schedule.sections.set(sections)
            return Response(
                {"message": "success", "id": schedule.id}, status=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            return Response(
                {
                    "detail": "IntegrityError encountered while trying to create: "
                    + str(e.__cause__)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self):
        sem = get_value("SEMESTER")
        queryset = Schedule.objects.filter(person=self.request.user, semester=sem)
        queryset = queryset.prefetch_related(Prefetch("sections", Section.with_reviews.all()),)
        return queryset
