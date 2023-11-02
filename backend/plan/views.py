import arrow
from accounts.authentication import PlatformAuthentication
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch, Q, Subquery
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django_auto_prefetching import AutoPrefetchViewSetMixin
from ics import Calendar as ICSCal
from ics import Event as ICSEvent
from ics.grammar.parse import ContentLine
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, Meeting, Section
from courses.serializers import CourseListSerializer, SectionDetailSerializer
from courses.util import find_possible_schedules, get_course_and_section, get_current_semester
from courses.views import get_accepted_friends
from PennCourses.docs_settings import PcxAutoSchema
from PennCourses.settings.base import PATH_REGISTRATION_SCHEDULE_NAME
from plan.management.commands.recommendcourses import (
    clean_course_input,
    recommend_courses,
    retrieve_course_clusters,
    vectorize_user,
    vectorize_user_by_courses,
)
from plan.models import PrimarySchedule, Schedule
from plan.serializers import PrimaryScheduleSerializer, ScheduleSerializer


@api_view(["POST"])
@schema(
    PcxAutoSchema(
        response_codes={
            "recommend-courses": {
                "POST": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Response returned successfully.",
                    201: "[UNDOCUMENTED]",
                    400: "Invalid curr_courses, past_courses, or n_recommendations (see response).",
                }
            }
        },
        override_request_schema={
            "recommend-courses": {
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
            "recommend-courses": {
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


class PrimaryScheduleViewSet(viewsets.ModelViewSet):
    """
    list: Get the primary schedule for the current user as well as primary
    schedules of the user's friends.

    create: Create/update/delete the primary schedule for the current user.
    """

    model = PrimarySchedule
    queryset = PrimarySchedule.objects.none()
    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated]
    serializer_class = PrimaryScheduleSerializer

    def get_queryset(self):
        return PrimarySchedule.objects.filter(
            Q(user=self.request.user)
            | Q(user_id__in=Subquery(get_accepted_friends(self.request.user).values("id")))
        ).prefetch_related(
            Prefetch("schedule__sections", Section.with_reviews.all()),
            "schedule__sections__associated_sections",
            "schedule__sections__instructors",
            "schedule__sections__meetings",
            "schedule__sections__meetings__room",
        )

    schema = PcxAutoSchema(
        response_codes={
            "primary-schedules-list": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Primary schedule (and friend's schedules) "
                    "retrieved successfully.",
                },
                "POST": {
                    201: "Primary schedule updated successfully.",
                    400: "Invalid schedule in request.",
                },
            },
        },
        override_request_schema={
            "primary-schedules-list": {
                "POST": {
                    "type": "object",
                    "properties": {
                        "schedule_id": {
                            "type": "integer",
                            "description": (
                                "The ID of the schedule you want to make primary "
                                "(or null to unset)."
                            ),
                        },
                    },
                }
            }
        },
    )

    def create(self, request):
        res = {}
        user = request.user
        schedule_id = request.data.get("schedule_id")
        if not schedule_id:
            # Delete primary schedule
            primary_schedule_entry = self.get_queryset().filter(user=user).first()
            if primary_schedule_entry:
                primary_schedule_entry.delete()
                res["message"] = "Primary schedule successfully unset"
            res["message"] = "Primary schedule was already unset"
        else:
            schedule = Schedule.objects.filter(person_id=user.id, id=schedule_id).first()
            if not schedule:
                res["message"] = "Schedule does not exist"
                return JsonResponse(res, status=status.HTTP_400_BAD_REQUEST)

            primary_schedule_entry = self.get_queryset().filter(user=user).first()
            if primary_schedule_entry:
                primary_schedule_entry.schedule = schedule
                primary_schedule_entry.save()
                res["message"] = "Primary schedule successfully updated"
            else:
                PrimarySchedule.objects.create(user=user, schedule=schedule)
                res["message"] = "Primary schedule successfully created"

        return JsonResponse(res, status=status.HTTP_200_OK)


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
    The `id` path parameter (an integer) specifies which schedule you want to update. [You can also
    pass `path` for the `id` path parameter, in order to create/update a Path Registration schedule
    for the user (the name of the schedule must be `Path Registration`, and you must be
    authenticated via Platform's token auth for IPC, e.g. from Penn Mobile).] If a schedule with
    the specified id does not exist, a 404 is returned. In the body of the PUT, use the same format
    as a POST request (see the Create Schedule docs).
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
            "schedules-list": {
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
            "schedules-detail": {
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
    def get_sections(data, skip_missing=False):
        raw_sections = []
        if "meetings" in data:
            raw_sections = data.get("meetings")
        elif "sections" in data:
            raw_sections = data.get("sections")
        sections = []
        for s in raw_sections:
            try:
                _, section = get_course_and_section(s.get("id"), s.get("semester"))
                sections.append(section)
            except ObjectDoesNotExist as e:
                if skip_missing:
                    continue
                else:
                    raise e
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

    def validate_name(self, request, existing_schedule=None, allow_path=False):
        if PATH_REGISTRATION_SCHEDULE_NAME in [
            request.data.get("name"),
            existing_schedule and existing_schedule.name,
        ] and not (
            allow_path and isinstance(request.successful_authenticator, PlatformAuthentication)
        ):
            raise PermissionDenied(
                "You cannot create/update/delete a schedule with the name "
                + PATH_REGISTRATION_SCHEDULE_NAME
            )

    def destroy(self, request, *args, **kwargs):
        self.validate_name(request, existing_schedule=self.get_object())
        return super().destroy(request, *args, **kwargs)

    def update(self, request, pk=None):
        from_path = pk == "path"
        if not from_path and (not pk or not Schedule.objects.filter(id=pk).exists()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            if from_path:
                schedule, _ = self.get_queryset().get_or_create(
                    name=PATH_REGISTRATION_SCHEDULE_NAME,
                    defaults={"person": self.request.user, "semester": get_current_semester},
                )
            else:
                schedule = self.get_queryset().get(id=pk)
        except Schedule.DoesNotExist:
            return Response(
                {"detail": "You do not have access to the specified schedule."},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.validate_name(request, existing_schedule=schedule, allow_path=from_path)

        try:
            sections = self.get_sections(request.data, skip_missing=from_path)
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
            schedule.name = (
                PATH_REGISTRATION_SCHEDULE_NAME if from_path else request.data.get("name")
            )
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

        self.validate_name(request)

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


class CalendarAPIView(APIView):
    schema = PcxAutoSchema(
        custom_path_parameter_desc={
            "calendar-view": {
                "GET": {"schedule_pk": "The PCP id of the schedule you want to export."},
            },
        },
        response_codes={
            "calendar-view": {
                "GET": {
                    200: "Schedule exported successfully",
                },
            },
        },
        override_response_schema={
            "calendar-view": {
                "GET": {
                    200: {
                        "media_type": "text/calendar",
                        "type": "string",
                        "description": "A calendar file in ICS format",
                    }
                }
            }
        },
    )

    def get(self, *args, **kwargs):
        """
        Return a .ics file of the user's selected schedule
        """
        schedule_pk = kwargs["schedule_pk"]

        schedule = (
            Schedule.objects.filter(pk=schedule_pk)
            .prefetch_related("sections", "sections__meetings")
            .first()
        )

        if not schedule:
            return Response({"detail": "Invalid schedule"}, status=status.HTTP_403_FORBIDDEN)

        day_mapping = {"M": "MO", "T": "TU", "W": "WE", "R": "TH", "F": "FR"}

        calendar = ICSCal(creator="Penn Labs")
        calendar.extra.append(ContentLine(name="X-WR-CALNAME", value=f"{schedule.name} Schedule"))

        for section in schedule.sections.all():
            e = ICSEvent()
            e.name = section.full_code
            e.created = timezone.now()

            days = []
            for meeting in section.meetings.all():
                days.append(day_mapping[meeting.day])
            first_meeting = list(section.meetings.all())[0]

            start_time = str(Meeting.int_to_time(first_meeting.start))
            end_time = str(Meeting.int_to_time(first_meeting.end))

            if not start_time:
                start_time = ""
            if not end_time:
                end_time = ""

            if first_meeting.start_date is None:
                start_datetime = ""
                end_datetime = ""
            else:
                start_datetime = first_meeting.start_date + " "
                end_datetime = first_meeting.start_date + " "

            if int(first_meeting.start) < 10:
                start_datetime += "0"
            if int(first_meeting.end) < 10:
                end_datetime += "0"

            start_datetime += start_time
            end_datetime += end_time

            e.begin = arrow.get(
                start_datetime, "YYYY-MM-DD HH:mm A", tzinfo="America/New York"
            ).format("YYYYMMDDTHHmmss")
            e.end = arrow.get(end_datetime, "YYYY-MM-DD HH:mm A", tzinfo="America/New York").format(
                "YYYYMMDDTHHmmss"
            )
            end_date = arrow.get(
                first_meeting.end_date, "YYYY-MM-DD", tzinfo="America/New York"
            ).format("YYYYMMDDTHHmmss")

            e.extra.append(
                ContentLine(
                    "RRULE",
                    {},
                    f'FREQ=WEEKLY;UNTIL={end_date}Z;WKST=SU;BYDAY={",".join(days)}',
                )
            )

            calendar.events.add(e)

        response = HttpResponse(calendar, content_type="text/calendar")
        response["Content-Disposition"] = "attachment; pcp-schedule.ics"
        return response


class AutomaticCourseScheduler(APIView):

    schema = PcxAutoSchema(
        response_codes={
            "calendar-view": {
                "POST": {
                    200: "Possible schedules found successfully",
                    400: "Courses do not exist",
                    404: "Cannot find any possible schedules",
                },
            },
        },
    )

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        courses = request.data.get("courses")
        semester = request.data.get("semester")
        breaks = request.data.get("breaks")
        cred_limit = request.data.get("credit_limit")
        try:
            course_objects = Course.objects.filter(full_code__in=courses, semester=semester).all()
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more courses not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sections_query = Section.objects.filter(course__in=course_objects)
            sections = sections_query.all()
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sections_json = SectionDetailSerializer(sections, many=True).data
        class_sections = {}
        for section in sections_json:
            course_code = "-".join(section["id"].split("-")[0:2])
            if course_code not in class_sections.keys():
                class_sections[course_code] = [section]
            else:
                class_sections[course_code].append(section)

        contin = True
        ticker = 0
        while (ticker < 6) and contin:
            data = find_possible_schedules(class_sections, cred_limit, breaks)
            if len(data) == 0:
                ticker += 1
            else:
                contin = False
        if len(data) == 0:
            return Response([], status=status.HTTP_404_NOT_FOUND)
        section_hash = {}
        for s in sections:
            section_hash[s.full_code] = s
        output = []
        for (i, schedule) in enumerate(data):
            a = []
            for section in schedule:
                a.append(section_hash[section[0]])
            output.append(SectionDetailSerializer(a, many=True, read_only=False).data)
            if i >= 5:
                break

        return Response(output, status=status.HTTP_200_OK)
