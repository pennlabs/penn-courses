from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch, Q
from backend.courses.models import User
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

from courses.models import Course, Section
from courses.serializers import CourseListSerializer
from courses.util import get_course_and_section, get_current_semester
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from plan.management.commands.recommendcourses import (
    clean_course_input,
    recommend_courses,
    retrieve_course_clusters,
    vectorize_user,
    vectorize_user_by_courses,
)
from plan.models import Schedule
from plan.serializers import ScheduleSerializer


@api_view(["POST"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("recommend-courses"): {
                "POST": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Response returned successfully.",
                    201: "[UNDOCUMENTED]",
                    400: "Invalid curr_courses, past_courses, or n_recommendations (see response).",
                }
            }
        },
        override_request_schema={
            reverse_func("recommend-courses"): {
                "POST": {
                    "type": "object",
                    "properties": {
                        "curr_courses": {
                            "type": "array",
                            "description": (
                                "An array of courses the user is currently planning to "
                                "take, each specified by its string full code, of the form "
                                "DEPT-XXX, e.g. CIS-120."
                            ),
                            "items": {"type": "string"},
                        },
                        "past_courses": {
                            "type": "array",
                            "description": (
                                "An array of courses the user has previously taken, each "
                                "specified by its string full code, of the form DEPT-XXX, "
                                "e.g. CIS-120."
                            ),
                            "items": {"type": "string"},
                        },
                        "n_recommendations": {
                            "type": "integer",
                            "description": (
                                "The number of course recommendations you want returned. "
                                "Defaults to 5."
                            ),
                        },
                    },
                }
            }
        },
        override_response_schema={
            reverse_func("recommend-courses"): {
                "POST": {
                    200: {"type": "array", "items": {"$ref": "#/components/schemas/CourseList"}}
                }
            }
        },
    )
)
@permission_classes([IsAuthenticated])
def recommend_courses_view(request):
    """
    This route will optionally take in current and past courses. In order to
    make recommendations solely on the user's courses in past and current PCP schedules, simply
    omit both the curr_courses and past_courses fields in your request.
    Otherwise, in order to specify past and current courses,
    include a "curr-courses" and/or "past_courses" attribute in the request that should each contain
    an array of string course full codes of the form DEPT-XXX (e.g. CIS-120).
    If successful, this route will return a list of recommended courses, with the same schema
    as the List Courses route, starting with the most relevant course. The number of
    recommended courses returned can be specified using the n_recommendations attribute in the
    request body, but if this attribute is omitted, the default will be 5.
    If n_recommendations is not an integer, or is <=0, a 400 will be returned.
    If curr_courses contains repeated courses or invalid courses or non-current courses, a
    400 will be returned.
    If past_courses contains repeated courses or invalid courses, a 400 will be returned.
    If curr_courses and past_courses contain overlapping courses, a 400 will be returned.
    """

    user = request.user
    curr_courses = request.data.get("curr_courses", None)
    curr_courses = curr_courses if curr_courses is not None else []
    past_courses = request.data.get("past_courses", None)
    past_courses = past_courses if past_courses is not None else []
    n_recommendations = request.data.get("n_recommendations", 5)

    # input validation
    try:
        n_recommendations = int(n_recommendations)
    except ValueError:
        return Response(
            f"n_recommendations: {n_recommendations} is not int",
            status=status.HTTP_400_BAD_REQUEST,
        )
    if n_recommendations <= 0:
        return Response(
            f"n_recommendations: {n_recommendations} <= 0",
            status=status.HTTP_400_BAD_REQUEST,
        )

    course_clusters = retrieve_course_clusters()

    (
        cluster_centroids,
        clusters,
        curr_course_vectors_dict,
        past_course_vectors_dict,
    ) = course_clusters

    if curr_courses or past_courses:
        try:
            user_vector, user_courses = vectorize_user_by_courses(
                clean_course_input(curr_courses),
                clean_course_input(past_courses),
                curr_course_vectors_dict,
                past_course_vectors_dict,
            )
        except ValueError as e:
            return Response(
                str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        user_vector, user_courses = vectorize_user(
            user, curr_course_vectors_dict, past_course_vectors_dict
        )

    recommended_course_codes = recommend_courses(
        curr_course_vectors_dict,
        cluster_centroids,
        clusters,
        user_vector,
        user_courses,
        n_recommendations,
    )

    queryset = Course.with_reviews.filter(
        semester=get_current_semester(), full_code__in=recommended_course_codes
    )
    queryset = queryset.prefetch_related(
        Prefetch(
            "sections",
            Section.with_reviews.all()
            .filter(credits__isnull=False)
            .filter(Q(status="O") | Q(status="C"))
            .distinct()
            .prefetch_related("course", "meetings__room"),
        )
    )

    return Response(
        CourseListSerializer(
            queryset,
            many=True,
        ).data,
        status=status.HTTP_200_OK,
    )

# Function-Based Views for Sharing Schedules

@permission_classes([IsAuthenticated])
def setSharedSchedule(request):
    res = {}
    # verify that the user and the schedule exist and set it as the primary for 
    # for the passed in user
    user = get_object_or_404(User, pk=request.user_id)
    schedule = get_object_or_404(Schedule, pk=request.schedule_id)
    if (not user or not schedule):
        res['message'] = 'User/Schedule does not exist'
        return JsonResponse(res, status=400)
    
    # check syntax for this but ensure that the schedule belongs to the user
    if (schedule.person != user):
        res['message'] = 'Schedule does not belong to user'
        return JsonResponse(res, status=400)

    # set the schedule as the primary schedule for the user (and set old shared to false)
    old_shared_schedule = Schedule.objects.filter(person=user, is_shared=True)
    if (old_shared_schedule):
        old_shared_schedule.is_shared = False
        old_shared_schedule.save()
    schedule.is_shared = True
    schedule.save()
    res['message'] = 'Schedule set as shared'
    # return successful response code once set
    return JsonResponse(res)

    # return HttpResponseBadRequest("Bad response, user does not exists")
    # return HttpResponseBadRequest("Bad response, schedule does not exist")

@permission_classes([IsAuthenticated])
def getSharedSchedule(request):
    res = {}
    # verify that the user exist and retrieve the primary schedule associated with them
    # and that the schedule still exists (in the case that the schedule was deleted)

    user = get_object_or_404(User, pk=request.user_id)
    if (not user):
        res['message'] = 'User does not exist'
        return JsonResponse(res, status=400)
    
    schedule = Schedule.objects.filter(person=user, is_shared=True)
    if (not schedule):
        res['message'] = 'No shared schedule for user'
        return JsonResponse(res, status=400)

    # return the schedule
    res = model_to_dict(schedule)
    res["message"] = "Shared schedule retrieved."
    # return successful response code once set
    return JsonResponse(res)

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
    objects with minimum fields `id` (dash-separated, e.g. `CIS-121-001`) and `semester`
    (5 character string, e.g. `2020A`).  If any of the sections are invalid, a 404 is returned
    with data `{"detail": "One or more sections not found in database."}`.  If any two sections in
    the `sections` list have differing semesters, a 400 is returned.

    Optionally, you can also include a `semester` field (5 character string, e.g. `2020A`) in the
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
        response_codes={
            reverse_func("schedules-list"): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Schedules listed successfully.",
                },
                "POST": {
                    201: "Schedule successfully created.",
                    200: "Schedule successfully updated (a schedule with the "
                    "specified id already existed).",
                    400: "Bad request (see description above).",
                },
            },
            reverse_func("schedules-detail", args=["id"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Successful retrieve "
                    "(the specified schedule exists).",
                    404: "No schedule with the specified id exists.",
                },
                "PUT": {
                    200: "Successful update (the specified schedule was found and updated).",
                    400: "Bad request (see description above).",
                    404: "No schedule with the specified id exists.",
                },
                "DELETE": {
                    204: "Successful delete (the specified schedule was found and deleted).",
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

    def update(self, request, pk=None):
        if not Schedule.objects.filter(id=pk).exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            schedule = self.get_queryset().get(id=pk)
        except Schedule.DoesNotExist:
            return Response(
                {"detail": "You do not have access to the specified schedule."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            sections = self.get_sections(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        semester_check_response = self.check_semester(request.data, sections)
        if semester_check_response is not None:
            return semester_check_response

        try:
            schedule.person = request.user
            schedule.semester = request.data.get("semester", get_current_semester())
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
        if Schedule.objects.filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))

        try:
            sections = self.get_sections(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        semester_check_response = self.check_semester(request.data, sections)
        if semester_check_response is not None:
            return semester_check_response

        try:
            if (
                "id" in request.data
            ):  # Also from above we know that this id does not conflict with existing schedules.
                schedule = self.get_queryset().create(
                    person=request.user,
                    semester=request.data.get("semester", get_current_semester()),
                    name=request.data.get("name"),
                    id=request.data.get("id"),
                )
            else:
                schedule = self.get_queryset().create(
                    person=request.user,
                    semester=request.data.get("semester", get_current_semester()),
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

    queryset = Schedule.objects.none()  # included redundantly for docs

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
