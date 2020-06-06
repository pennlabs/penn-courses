from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from django_auto_prefetching import AutoPrefetchViewSetMixin
from options.models import get_value
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from PennCourses.docs_settings import PcxAutoSchema
from courses.models import Section
from courses.util import get_course_and_section
from courses.views import CourseList
from plan.filters import CourseSearchFilterBackend
from plan.models import Schedule
from plan.search import TypedCourseSearchBackend
from plan.serializers import ScheduleSerializer


class CourseListSchema(PcxAutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET":
            operation["parameters"].extend([])
        return operation


class CourseListSearch(CourseList):
    """
    The main API endpoint for PCP. Without any GET parameters, it simply returns all courses for
    a given semester. Authentication not required.
    """

    schema = CourseListSchema()

    filter_backends = [TypedCourseSearchBackend, CourseSearchFilterBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")


class ScheduleViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    list:
    Get a list of all the logged-in user's schedules for the current semester.  Normally, the
    response code is 200. Each object in the returned list is of the same form as the object
    returned by Retrieve Schedule, detailed below.
    <span style="color:red;">User authentication required</span>.

    retrieve:
    Get one of the logged-in user's schedules for the current semester, using the schedule's ID.
    If a schedule with the specified ID exists, a 200 response code is returned, along with
    an object of the same form as the objects in the list returned by List Schedule,
    detailed above. If the given id does not exist, a 404 is returned, along with
    data `{'detail': 'Not found.'}`.n<span style="color:red;">User authentication required</span>.

    create:
    This route will return a 201 if it succeeds, and a JSON in the same format as if you were
    to get the schedule you just posted (in the same format as returned
    by Retrieve Schedule).  At a minimum, you must include the `title` and
    `sections` (or `meetings`) list. Title is the name of the schedule (all names must be distinct
    for a single user in a single semester; otherwise in the POST a

    Note that your posted object can include either a `sections`
    field or a `meetings` field to list all sections you would like to be in the schedule.
    If both fields exist in the object, only `meetings` will be considered.  In all cases,
    the field in question will be renamed to `sections` so that will be the field name whenever
    you GET from the server. (Sorry for this confusing behavior, it is grandfathered in
    from when the PCP frontend was referring to sections as meetings, before schedules were
    stored on the backend.)

    <span style="color:red;">User authentication required</span>.
    - `title` - must be unique for a given user in this semester.
    - `meetings[*].semester` -

    update:
    <span style="color:red;">User authentication required</span>.

    delete:
    <span style="color:red;">User authentication required</span>.
    """

    schema = PcxAutoSchema()
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
