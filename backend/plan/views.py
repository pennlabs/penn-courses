from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import plan.examples as examples
from courses.models import Section
from courses.util import get_course_and_section, get_current_semester
from courses.views import CourseList
from PennCourses.docs_settings import PcxAutoSchema
from plan.filters import CourseSearchFilterBackend
from plan.models import Schedule
from plan.search import TypedCourseSearchBackend
from plan.serializers import ScheduleSerializer


class CourseListSearch(CourseList):
    """
    The main course API endpoint for PCP. Without any GET parameters, it simply returns all courses
    for a given semester. There are a few filter query parameters which constitute ranges of
    floating-point numbers. The values for these are <min>-<max> , with minimum excluded.
    For example, looking for classes in the range of 0-2.5 in difficulty, you would add the
    parameter difficulty=0-2.5. If you are a backend developer, you can find these filters in
    backend/plan/filters.py/CourseSearchFilterBackend. If you are reading the frontend docs,
    these filters are listed below in the query parameters list (with description starting with
    "Filter").
    """

    schema = PcxAutoSchema(
        examples=examples.CourseListSearch_examples,
        response_codes={
            "/api/plan/courses/": {"GET": {200: "[SCHEMA]Courses listed successfully."}}
        },
    )

    filter_backends = [TypedCourseSearchBackend, CourseSearchFilterBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")


class ScheduleViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    list:
    Get a list of all the logged-in user's schedules for the current semester.  Normally, the
    response code is 200. Each object in the returned list is of the same form as the object
    returned by Retrieve Schedule.

    retrieve:
    Get one of the logged-in user's schedules for the current semester, using the schedule's ID.
    If a schedule with the specified ID exists, a 200 response code is returned, along with
    the schedule object.
    If the given id does not exist, a 404 is returned.

    create:
    Use this route to create a schedule for the authenticated user.
    This route will return a 201 if it succeeds (or a 200 if the POST specifies an id which already
    is associated with a schedule, causing that schedule to be updated), with a JSON in the same
    format as if you were to get the schedule you just posted (the 200 response schema for Retrieve
    Schedule). At a minimum, you must include the `name` and `sections` list (`meetings` can be
    substituted for `sections`; if you don't know why, ignore this and just use `sections`,
    or see below for an explanation... TLDR: it is grandfathered in from the old version of PCP).
    The `name` is the name of the schedule (all names must be distinct for a single user in a
    single semester; otherwise the response will be a 400). The sections list must be a list of
    objects with minimum fields `id` (dash-separated, e.g. "CIS-121-001") and `semester`
    (5 character string, e.g. '2020A').  If any of the sections are invalid, a 404 is returned
    with data `{"detail": "One or more sections not found in database."}`.  If any two sections in
    the `sections` list have differing semesters, a 400 is returned.

    Optionally, you can also include a `semester` field (5 character string, e.g. '2020A') in the
    posted object, which will set the academic semester which the schedule is planning.  If the
    `semester` field is omitted, the semester of the first section in the `sections` list will be
    used (or if the `sections` list is empty, the current semester will be used).  If the
    schedule's semester differs from any of the semesters of the sections in the `sections` list,
    a 400 will be returned.

    Optionally, you can also include an `id` field (an integer) in the posted object; if you
    include it, it will update the schedule with the given id (if such a schedule exists),
    or if the schedule does not exist, it will create a new schedule with that id.

    Note that your posted object can include either a `sections` field or a `meetings` field to
    list all sections you would like to be in the schedule (mentioned above).
    If both fields exist in the object, only `meetings` will be considered.  In all cases,
    the field in question will be renamed to `sections`, so that will be the field name whenever
    you GET from the server. (Sorry for this confusing behavior, it is grandfathered in
    from when the PCP frontend was referring to sections as meetings, before schedules were
    stored on the backend.)

    update:
    Send a put request to this route to update a specific schedule.
    The `id` path parameter (an integer) specifies which schedule you want to update.  If a
    schedule with the specified id does not exist, a 404 is returned. In the body of the PUT,
    use the same format as a POST request (see the create schedule docs).
    This is an alternate way to update schedules (you can also just include the id field
    in a schedule when you post and it will update that schedule if the id exists).  Note that in a
    put request the  id field in the putted object is ignored; the id taken from the route
    always takes precedence. If the request succeeds, it will return a 200 and a JSON in the same
    format as if you were to get the schedule you just updated (in the same format as returned by
    the GET /schedules/ route).

    delete:
    Send a delete request to this route to delete a specific schedule.  The `id` path parameter
    (an integer) specifies which schedule you want to update.  If a schedule with the specified
    id does not exist, a 404 is returned.  If the delete is successful, a 204 is returned.
    """

    schema = PcxAutoSchema(
        examples=examples.ScheduleViewSet_examples,
        response_codes={
            "/api/plan/schedules/": {
                "GET": {200: "[SCHEMA]Schedules listed successfully.",},
                "POST": {
                    201: "Schedule successfully created.",
                    200: "Schedule successfully updated (a schedule with the "
                    "specified id already existed).",
                    400: "Bad request (see description above).",
                },
            },
            "/api/plan/schedules/{id}/": {
                "GET": {
                    200: "[SCHEMA]Successful retrieve (the specified schedule exists).",
                    404: "No schedule with the specified id exists.",
                },
                "PUT": {
                    200: "Successful update (the specified schedule exists "
                    "and was successfully updated).",
                    400: "Bad request (see description above).",
                    404: "No schedule with the specified id exists.",
                },
                "DELETE": {
                    204: "[SCHEMA]Successful delete (the specified schedule existed "
                    "and was successfully deleted).",
                    404: "No schedule with the specified id exists.",
                },
            },
        },
    )

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
            data["semester"] = get_current_semester()

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
            return Response({"message": "success", "id": schedule.id}, status=status.HTTP_200_OK)
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

    queryset = (
        Schedule.objects.none()
    )  # used to help out the AutoSchema in generating documentation

    def get_queryset(self):
        sem = get_current_semester()
        queryset = Schedule.objects.filter(person=self.request.user, semester=sem)
        queryset = queryset.prefetch_related(
            Prefetch("sections", Section.with_reviews.all()),
            "sections__associated_sections",
            "sections__instructors",
            "sections__meetings",
            "sections__meetings__room",
        )
        return queryset
