from django.db.models import Q

from rest_framework import filters

from courses.models import Requirement
from options.models import get_value


def requirement_filter(queryset, req_ids, semester):
    query = Q()
    for req_id in req_ids.split(","):
        code, school = req_id.split("@")
        try:
            requirement = Requirement.objects.get(semester=semester, code=code, school=school)
        except Requirement.DoesNotExist:
            continue
        query &= Q(id__in=requirement.satisfying_courses.all())
    queryset = queryset.filter(query)

    return queryset


def bound_filter(field):
    def filter_bounds(queryset, bounds, semester=None):
        lower_bound, upper_bound = bounds.split("-")
        lower_bound = float(lower_bound)
        upper_bound = float(upper_bound)

        return queryset.filter(
            Q(**{f"{field}__gte": lower_bound, f"{field}__lte": upper_bound,})
            | Q(**{f"{field}__isnull": True})
        )

    return filter_bounds


def choice_filter(field):
    def filter_choices(queryset, choices, semester=None):
        query = Q()
        for choice in choices.split(","):
            query = query | Q(**{field: choice})
        return queryset.filter(query)

    return filter_choices


class CourseSearchFilterBackend(filters.BaseFilterBackend):
    def get_semester(self, request):
        semester = self.kwargs.get("semester", "current")
        if semester == "current":
            semester = get_value("SEMESTER", "all")

        return semester

    def filter_queryset(self, request, queryset, view):
        filters = {
            "requirements": requirement_filter,
            "cu": choice_filter("sections__credits"),
            "activity": choice_filter("sections__activity"),
            "course_quality": bound_filter("course_quality"),
            "instructor_quality": bound_filter("instructor_quality"),
            "difficulty": bound_filter("difficulty"),
        }

        for field, filter_func in filters.items():
            param = request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param, self.get_semester())

        return queryset.distinct()

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "type",
                "required": False,
                "in": "query",
                "description": "Can specify what kind of query to run. Course queries are faster, keyword queries look against professor name and course title.",
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
                "description": "Filter courses by comma-separated requirements, ANDed together. Use `/requirements` endpoint to get requirement IDs.",
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
                "description": "Filter course difficulty to be within the given range.",
                "schema": {"type": "string"},
                "example": "1-2.5",
            },
            {
                "name": "course_quality",
                "required": False,
                "in": "query",
                "description": "Filter course quality to be within the given range.",
                "schema": {"type": "string"},
                "example": "1-2.5",
            },
            {
                "name": "instructor_quality",
                "required": False,
                "in": "query",
                "description": "Filter instructor quality to be within the given range.",
                "schema": {"type": "string"},
                "example": "1-2.5",
            },
        ]
