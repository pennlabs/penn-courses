from django.db.models import Q
from rest_framework import filters

from courses.models import Requirement
from courses.util import get_current_semester
from decimal import Decimal


def requirement_filter(queryset, req_ids):
    query = Q()
    for req_id in req_ids.split(","):
        code, school = req_id.split("@")
        try:
            requirement = Requirement.objects.get(
                code=code, school=school, semester=get_current_semester()
            )
        except Requirement.DoesNotExist:
            continue
        query &= Q(id__in=requirement.satisfying_courses.all())
    queryset = queryset.filter(query)

    return queryset


def day_filter(queryset, days):
    # TODO: fix this query
    queryset = queryset.filter(sections__meetings__day__in=days.split())
    return queryset


def time_filter(queryset, time_range):
    start_time, end_time = time_range.split("-")
    # TODO: fix this query
    queryset = queryset.filter(
        Q(
            sections__earliest_meeting__gte=Decimal(start_time),
            sections__latest_meeting__lte=Decimal(end_time),
        )
        | Q(sections__meetings__isnull=True)
    )
    return queryset


def bound_filter(field):
    def filter_bounds(queryset, bounds):
        lower_bound, upper_bound = bounds.split("-")
        lower_bound = float(lower_bound)
        upper_bound = float(upper_bound)
        return queryset.filter(
            Q(**{f"{field}__gte": lower_bound, f"{field}__lte": upper_bound,})
            | Q(**{f"{field}__isnull": True})
        )

    return filter_bounds


def choice_filter(field):
    def filter_choices(queryset, choices):
        query = Q()
        for choice in choices.split(","):
            query = query | Q(**{field: choice})
        return queryset.filter(query)

    return filter_choices


class CourseSearchFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filters = {
            "requirements": requirement_filter,
            "cu": choice_filter("sections__credits"),
            "activity": choice_filter("sections__activity"),
            "course_quality": bound_filter("course_quality"),
            "instructor_quality": bound_filter("instructor_quality"),
            "difficulty": bound_filter("difficulty"),
            "days": day_filter,
            "time": time_filter,
        }

        for field, filter_func in filters.items():
            param = request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param)

        return queryset.distinct()

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "type",
                "required": False,
                "in": "query",
                "description": "Can specify what kind of query to run. Course queries are faster, "
                "keyword queries look against professor name and course title.",
                "schema": {
                    "type": "string",
                    "default": "auto",
                    "enum": ["auto", "course", "keyword"],
                },
            },
            {
                "name": "requirements",
                "required": False,
                "in": "query",
                "description": "Filter courses by comma-separated requirements, ANDed together. "
                "Use `/requirements` endpoint to get requirement IDs.",
                "schema": {"type": "string"},
                "example": "SS@SEAS,H@SEAS",
            },
            {
                "name": "cu",
                "required": False,
                "in": "query",
                "description": "Filter course units to be within the given range.",
                "schema": {"type": "string"},
                "example": "0-0.5",
            },
            {
                "name": "difficulty",
                "required": False,
                "in": "query",
                "description": (
                    "Filter course difficulty (average across all reviews) to be within "
                    "the given range."
                ),
                "schema": {"type": "string"},
                "example": "1-2.5",
            },
            {
                "name": "course_quality",
                "required": False,
                "in": "query",
                "description": (
                    "Filter course quality (average across all reviews) to be within "
                    "the given range."
                ),
                "schema": {"type": "string"},
                "example": "2.5-4",
            },
            {
                "name": "instructor_quality",
                "required": False,
                "in": "query",
                "description": (
                    "Filter instructor quality (average across all reviews) to be "
                    "within the given range."
                ),
                "schema": {"type": "string"},
                "example": "2.5-4",
            },
            {
                "name": "days",
                "required": False,
                "in": "query",
                "description": ("Filter meetings to be within the specified set of days."),
                "schema": {"type": "string"},
                "example": "TWR",
            },
            {
                "name": "time",
                "required": False,
                "in": "query",
                "description": (
                    "Filter meeting times to be within the specified range (specifying times with "
                    "decimal numbers between 0 and 23.9... (representing the hour of the day in ET)."
                ),
                "schema": {"type": "string"},
                "example": "11.5-18",
            },
        ]
