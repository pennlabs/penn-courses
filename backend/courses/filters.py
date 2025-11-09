from decimal import Decimal

from django.core.exceptions import BadRequest
from django.db.models import Count, Q
from django.db.models.expressions import F, Subquery
from rest_framework import filters

from courses.models import Meeting, Section
from courses.serializers import AdvancedSearchDataSerializer
from plan.models import Schedule


def section_ids_by_meeting_query(meeting_query):
    """
    Returns a queryset of the ids of sections for which all meetings pass the
    given meeting query.
    """
    return (
        Meeting.objects.filter(meeting_query)
        .values("section")
        .annotate(num_matching_meetings=Count("id"))
        .order_by()
        .filter(section__num_meetings=F("num_matching_meetings"))
        .values("section_id")
        .distinct()
    )


def course_ids_by_section_query(section_query):
    """
    Returns a queryset of the ids of courses for which at least one section
    of each activity type passes the given section query.
    """
    return (
        Section.objects.filter(section_query)
        .values("course")
        .annotate(num_matching_activities=Count("activity", distinct=True))
        .order_by()
        .filter(course__num_activities=F("num_matching_activities"))
        .values("course_id")
        .distinct()
    )


def meeting_filter(queryset, meeting_query):
    """
    Filters the given queryset of courses by the following condition:
    include a course only if the specified meeting filter
    (meeting_query, represented as a Q() query object)
    does not limit the set of section activities we can participate in for the course.
    For instance, if meeting_query=Q(day__in={"T","W","R"}),
    then we would include a course with lecture and recitation sections only if
    we could enroll in some lecture section and some recitation section and
    only have to attend meetings on Tuesdays, Wednesdays, and/or Thursdays.
    However, if the course had a lab section that only met on Fridays,
    we would no longer include the course (since we cannot attend the meetings of the
    lab section, and thus the set of course activities available to us is incomplete).
    """
    return queryset.filter(
        id__in=course_ids_by_section_query(
            Q(num_meetings=0) | Q(id__in=section_ids_by_meeting_query(meeting_query))
        )
    )


def _enum(field):
    """
    Constructs an enum filter function for the given field, operators, and values
    """

    def filter_enum(filter_condition):
        op = filter_condition["op"]
        values = filter_condition["value"]

        match op:
            case "is":
                return Q(**{field: values[0]})
            case "is_not":
                return ~Q(**{field: values[0]})
            case "is_any_of":
                return Q(**{f"{field}__in": set(values)})
            case "is_none_of":
                return ~Q(**{f"{field}__in": set(values)})
        return Q()

    return filter_enum


def _numeric(field):
    """
    Constructs a numeric filter function for the given field, operators, and values
    """

    def filter_numeric(filter_condition):
        op = filter_condition["op"]
        value = Decimal(filter_condition["value"])

        q = Q(**{f"{field}__isnull": True})

        match op:
            case "eq":
                return q | Q(**{field: value})
            case "neq":
                return q | ~Q(**{field: value})
            case _:
                return q | Q(**{f"{field}__{op}": value})

        return Q()

    return filter_numeric


def _boolean(field):
    def filter_boolean(filter_condition):
        value = filter_condition["value"]
        return Q(**{field: value})

    return filter_boolean


def _combine(op, q1, q2):
    match op:
        case "AND":
            return q1 & q2
        case "OR":
            return q1 | q2
    raise BadRequest(f"Invalid group operator: {op}")


def _is_open(filter_condition):
    """
    Filters the given queryset of courses by the following condition:
    include a course only if filtering its sections by `status="O"` does
    not does not limit the set of section activities we can participate in for the course.
    In other words, include only courses for which all activities have open sections.
    Note that for compatibility, this function can take additional positional
    arguments, but these are ignored.
    """
    return Q(id__in=course_ids_by_section_query(Q(status="O")))


def _fit_schedule(request):
    """
    Generates a schedule filter function that checks for proper
    authentication in the given request.
    """

    def filter_fit_schedule(filter_condition):
        schedule_id = filter_condition["value"]
        if not schedule_id:
            return Q()
        if not schedule_id.isdigit():
            return Q()
        if not request.user.is_authenticated:
            return Q()
        meetings = Meeting.objects.filter(
            section_id__in=Subquery(
                Schedule.objects.filter(id=int(schedule_id), person_id=request.user.id).values(
                    "sections__id"
                )
            )
        )
        q = Q()
        for meeting in meetings:
            q &= meeting.no_conflict_query
        return q

    return filter_fit_schedule


class CourseSearchAdvancedFilterBackend(filters.BaseFilterBackend):
    field_map = {
        "cu": _enum("sections__credits"),
        "activity": _enum("sections__activity"),
        "days": _enum("day"),
        "difficulty": _numeric("difficulty"),
        "course_quality": _numeric("course_quality"),
        "instructor_quality": _numeric("instructor_quality"),
        "start_time": _numeric("start"),
        "end_time": _numeric("end"),
        "is_open": _is_open,
        "fit_schedule": _fit_schedule(request=None),
        "attribute": _enum("attributes__code"),
    }

    meeting_fields = {"days", "start_time", "end_time", "fit_schedule"}

    def _apply_filters(self, request, queryset, filter_group):
        op = filter_group.get("op")
        children = filter_group.get("children", [])
        q = Q()
        meeting_q = Q()
        for child in children:
            child_q = Q()
            child_meeting_q = Q()
            if child["type"] == "group":
                child_q, child_meeting_q = self._apply_filters(request, queryset, child)
                q = _combine(op, q, child_q)
                meeting_q = _combine(op, meeting_q, child_meeting_q)
            else:
                field = child["field"]
                filter_func = self.field_map[field]

                if field == "fit_schedule":
                    filter_func = _fit_schedule(request)

                if field not in self.meeting_fields:
                    child_q = filter_func(child)
                    q = _combine(op, q, child_q)
                else:
                    child_meeting_q = filter_func(child)
                    meeting_q = _combine(op, meeting_q, child_meeting_q)

        return q, meeting_q

    def filter_queryset(self, request, queryset, view):
        q, meeting_q = self._apply_filters(request, queryset, request.data)
        queryset = queryset.filter(q)
        # Separate meeting filter for optimization
        if len(meeting_q) > 0:
            queryset = meeting_filter(queryset, meeting_q)

        return queryset.distinct("full_code")

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "search_data",
                "in": "body",
                "required": True,
                "description": "Advanced search parameters with query string and filters.",
                "schema": AdvancedSearchDataSerializer().data,
                "example": {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "activity",
                            "op": "is_any_of",
                            "value": ["LEC", "REC"],
                        },
                        {
                            "type": "numeric",
                            "field": "difficulty",
                            "op": "lte",
                            "value": 3,
                        },
                        {
                            "type": "enum",
                            "field": "attribute",
                            "op": "is_any_of",
                            "value": ["WUOM", "EMCI"],
                        },
                        {
                            "type": "group",
                            "op": "OR",
                            "children": [
                                {
                                    "type": "boolean",
                                    "field": "is_open",
                                    "value": True,
                                },
                                {
                                    "type": "enum",
                                    "field": "credit_units",
                                    "op": "is",
                                    "value": "1.0",
                                },
                            ],
                        },
                    ],
                },
            }
        ]
