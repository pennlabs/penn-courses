from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Prefetch, Q, F
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course, Section
from courses.serializers import CourseListSerializer, MiniSectionSerializer
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

from ortools.sat.python import cp_model
from collections import defaultdict

from courses.filters import (
    day_filter,
    time_filter,
    section_ids_by_meeting_query,
    course_ids_by_section_query,
)

@api_view(["POST"])
@schema(
    PcxAutoSchema(
        response_codes={
            reverse_func("recommend-schedules"): {
                "POST": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Response returned successfully.",
                    201: "[UNDOCUMENTED]",
                    400: "Invalid curr_courses, past_courses, or n_recommendations (see response).",
                }
            }
        },
        override_request_schema={
            reverse_func("recommend-schedules"): {
                "POST": {
                    "type": "object",
                    "properties": {
                        "num_schedules": {
                            "type": "integer",
                            "description": (
                                "The number of credits you want returned. "
                                "Defaults to 5.0."
                            ),
                        },
                        "num_credits": {
                            "type": "float",
                            "description": (
                                "The number of credits you want returned. "
                                "Defaults to 5.0."
                            ),
                        },
                        "min_courses": {
                            "type": "integer",
                            "description": (
                                "The number of courses you want returned. "
                            ),
                        },
                        "max_courses": {
                            "type": "integer",
                            "description": (
                                "The number of courses you want returned. "
                            ),
                        },
                        "locked_courses": {
                            "type": "array",
                            "description": (
                                "An array of courses the user is currently planning to "
                                "take, each specified by its string full code, of the form "
                                "DEPT-XXX, e.g. CIS-120."
                            ),
                            "items": {"type": "string"},
                        },
                        "locked_sections": {
                            "type": "array",
                            "description": (
                                "An array of courses the user is currently planning to "
                                "take, each specified by its string full code, of the form "
                                "DEPT-XXX, e.g. CIS-120."
                            ),
                            "items": {"type": "string"},
                        },
                        "avoid_courses": {
                            "type": "array",
                            "description": (
                                "An array of courses the user is currently planning to "
                                "take, each specified by its string full code, of the form "
                                "DEPT-XXX, e.g. CIS-120."
                            ),
                            "items": {"type": "string"},
                        },
                        "min_difficulty": {
                            "type": "boolean",
                            "description": (
                                "The number of courses you want returned. "
                            ),
                        },
                        "max_quality": {
                            "type": "boolean",
                            "description": (
                                "The number of courses you want returned. "
                            ),
                        },
                        "are_open": {
                            "type": "boolean",
                            "description": (
                                "... "
                            ),
                        },
                        "days": {
                            "type": "string",
                            "description": (
                                "..."
                            ),
                        },
                        "time": {
                            "type": "string",
                            "description": (
                                "..."
                            ),
                        },
                        "attributes": {
                            "type": "array",
                            "description": (
                                "..."
                            ),
                            "items": {"type": "object"},
                        }
                    },
                }
            }
        },
        # override_response_schema={
        #     reverse_func("recommend-schedules"): {
        #         "POST": {
        #             200: {"type": "array", "items": {"$ref": "#/components/schemas/CourseList"}}
        #         }
        #     }
        # },
    )
)
@permission_classes([IsAuthenticated])
def recommend_schedules_view(request):
    """
    """
    num_schedules = request.data.get("num_schedules", 1)

    num_credits = request.data.get("num_credits", 5.0)
    min_courses = request.data.get("min_courses", None)
    max_courses = request.data.get("max_courses", None)

    locked_courses = set(request.data.get("locked_courses", []))
    locked_sections = set(request.data.get("locked_sections", []))
    avoid_courses = set(request.data.get("avoid_courses", []))

    min_difficulty = request.data.get("min_difficulty", False)
    max_quality = request.data.get("max_quality", False)

    are_open = request.data.get("are_open", False)
    days = request.data.get("days", None)
    time = request.data.get("time", None)

    attributes = request.data.get("attributes", {})
    attribute_set = set([attribute["code"] for attribute in attributes])

    queryset = Course.with_reviews.filter(semester="2023A", sections__isnull=False).distinct()

    section_status_query = Q(status="O") if are_open else Q(status="O") | Q(status="C")
    section_query = section_status_query

    section_meeting_query = Q()
    if days:
        section_meeting_query &= day_filter(days)
    if time:
        section_meeting_query &= time_filter(time)
    if len(section_meeting_query) > 0:
        section_query &= Q(num_meetings=0) | Q(id__in=section_ids_by_meeting_query(section_meeting_query))

    section_locked_query = Q(full_code__in=locked_sections)
    section_query = section_query | section_locked_query # Note: Locked sections will ignore open / meeting constraints

    # Allows potentially filtering out locked courses -> Show warning on front-end if locked course will prevent feasible schedules
    queryset = queryset.filter(id__in=course_ids_by_section_query(section_query))
    # Last step - filter out crosslisted courses that aren't locked
    queryset = queryset.filter(Q(id=F('primary_listing__id')) | Q(full_code__in=locked_courses))

    queryset = queryset.prefetch_related(
        Prefetch(
            "sections",
            Section.with_reviews.all()
            .filter(credits__isnull=False)
            .filter(meetings__isnull=False)
            .filter(section_query)
            .distinct()
            .prefetch_related("meetings"),
        )
    )

    # Creates the model.
    model = cp_model.CpModel()

    # Creates the variables.
    courses = {}
    sections = {}
    all_section_intervals = []

    day_to_index = { "U": 0, "M": 1, "T": 2, "W": 3, "R": 4, "F": 5, "S": 6 }
    def meeting_to_interval(meeting):
        start_offset = day_to_index[meeting.day] * 24
        start, end = meeting.start, meeting.end
        if start >= 24:
            start -= 12
        if end >= 24:
            end -= 12
        start = int(100 * (start_offset + start))
        end = int(100 * (start_offset + end))
        duration = end - start
        return (start, duration)

    for course in queryset:
        courses[course.full_code] = model.NewBoolVar('course_%s' % (course.full_code))

        for section in course.sections.all():
            sections[section.full_code] = model.NewBoolVar('section_%s' % (section.full_code))

            for i, meeting in enumerate(section.meetings.all()):
                start, duration = meeting_to_interval(meeting)
                meeting_interval = model.NewOptionalFixedSizeIntervalVar(start, duration, sections[section.full_code], 'section_%s_interval_%d' % (section.full_code, i))
                all_section_intervals.append(meeting_interval)

    no_solution_response = Response(
        { 
            "detail": "No solution found." 
        }, 
        status=status.HTTP_400_BAD_REQUEST
    )
    if True in (c not in courses for c in locked_courses) or True in (s not in sections for s in locked_sections):
        return no_solution_response

    # Creates the constraints.
    schedule_courses = []
    schedule_credits = []
    section_scores = [] # Objective score
    schedule_attributes = defaultdict(list)

    for course in queryset:
        schedule_courses.append(courses[course.full_code])
        course_sections = defaultdict(set)

        for attribute in course.attributes.all():
            if attribute.code in attribute_set:
                schedule_attributes[attribute.code] += [1 * courses[course.full_code]]

        if course.full_code in locked_courses:
            model.Add(courses[course.full_code] == 1)
        
        if course.full_code in avoid_courses:
            model.Add(courses[course.full_code] == 0)

        if not course.sections.all():
            model.Add(courses[course.full_code] == 0)
        else:
            for section in course.sections.all():
                course_sections[section.activity].add(sections[section.full_code])
                schedule_credits.append(int(100 * section.credits) * sections[section.full_code])

                model.AddImplication(sections[section.full_code], courses[course.full_code])
                model.AddImplication(courses[course.full_code].Not(), sections[section.full_code].Not())

                if section.full_code in locked_sections:
                    model.Add(sections[section.full_code] == 1)
                else:
                    section_score = 0.0
                    if max_quality:
                        section_score += section.instructor_quality or 0.0
                    if min_difficulty:
                        section_score -= course.difficulty or 4.0
                    section_score = int(section_score * int(100 * section.credits))
                    section_scores.append(section_score * sections[section.full_code])

            for activity in course_sections:
                model.AddAtMostOne(course_sections[activity])
                model.AddAtLeastOne(course_sections[activity]).OnlyEnforceIf(courses[course.full_code])

    model.Add(sum(schedule_credits) == int(num_credits * 100))

    if min_courses:
        model.Add(sum(schedule_courses) >= min_courses)

    if max_courses:
        model.Add(sum(schedule_courses) <= min_courses)

    model.AddNoOverlap(all_section_intervals)

    for attribute in attributes:
        model.Add(sum(schedule_attributes[attribute["code"]]) == attribute["num"])

    # Creates a solver and solves the model.
    solver = cp_model.CpSolver()

    print("solving...")

    if max_quality or min_difficulty:
        model.Maximize(sum(section_scores))
        result = solver.Solve(model)
        if result == cp_model.OPTIMAL or result == cp_model.FEASIBLE:
            best_objective_bound = round(solver.ObjectiveValue())
            delta = int(min(0.25, num_schedules * 0.05) * abs(best_objective_bound))
            model.Proto().ClearField('objective')
            model.Add(sum(section_scores) >= best_objective_bound - delta)
        else:
            return no_solution_response

    # Sets a time limit of 10 seconds.
    solver.parameters.max_time_in_seconds = 10.0

    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True

    class SolutionHandler(cp_model.CpSolverSolutionCallback):
        def __init__(self, schedules, sections, limit):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.__schedules = schedules
            self.__sections = sections
            self.__solution_count = 0
            self.__solution_limit = limit

        def on_solution_callback(self):
            # TO-DO: OR-Tools needs to fix viewing optional variables (intervals) as different solutions?
            # self.__solution_count += 1
            recommended_schedule = [section for section in self.__sections if self.Value(self.__sections[section])]

            if True not in [set(recommended_schedule) == set(schedule) for schedule in self.__schedules]:
                print(recommended_schedule)
                self.__schedules += [recommended_schedule]
                self.__solution_count += 1

            if self.__solution_count >= self.__solution_limit:
                self.StopSearch()
        
        def solution_count(self):
            return self.__solution_count

    recommended_schedules = []
    solution_handler = SolutionHandler(recommended_schedules, sections, num_schedules)
    result = solver.Solve(model, solution_handler)

    if solution_handler.solution_count():
        recommended_schedules_data = []
        
        for schedule in recommended_schedules:
            queryset = Section.with_reviews.filter(course__semester="2023A", full_code__in=schedule)
            recommended_schedules_data.append(MiniSectionSerializer(queryset, many=True).data)
        
        return Response(
            {
                "results": solution_handler.solution_count(),
                "schedules": recommended_schedules_data,
            },
            status=status.HTTP_200_OK,
        )

    return no_solution_response

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
