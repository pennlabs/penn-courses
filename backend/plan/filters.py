from django.db.models import Q
from more_itertools import powerset
from rest_framework import filters

from courses.models import Requirement, Section, Course
from courses.util import get_current_semester


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
    # query = Q()
    # day_letters = [day for day in days]
    # all_days = [x for x in "MTWRFS"]
    # to_remove = list(set(all_days) - set(day_letters))
    # # all_secs = Course.objects.get(course__in=queryset)
    # # valid_sections = all_secs.exclude(meetings__day__in=to_remove)
    # sections = Section.objects.filter(course__in=list(queryset))
    # valid_sections = sections.exclude(meetings__day__in=to_remove)
    # queryset = queryset.filter(sections__in=list(valid_sections))
    #
    # # query &= Q(course.sections.exclude(meetings__day__in=to_remove))
    # # queryset = queryset.filter(query)
    # # all_days = list(powerset(day_letters))
    # # "MWF" in "F"
    # # combined_days = []
    # # for tup in all_days:
    # #     query = query | Q(sections__meetings__day=(''.join(tup)))
    # #     y = 15
    #     # combined_days.append(''.join(tup))
    # # queryset = queryset.filter(query) | queryset.filter(sections__meetings__isnull=True)
    # # queryset = queryset.filter(sections__in=list(valid_sections))
    # # days_to_remove = list(set(all_days) - set(day_letters))
    # # for day in days_to_remove:
    # #     queryset = queryset.exclude(sections__meetings__day__contains=day)
    # return queryset

    # if days == "MTWRFS":
    #     return queryset
    # for course in queryset.iterator():
    #     delete_all = True
    #     for section in course.sections.all():
    #         sec_invalid = False
    #         for meeting in section.meetings.all():
    #             meeting_days = meeting.day
    #             for day in meeting_days:
    #                 if day not in day_letters:
    #                     sec_invalid = True
    #         if not sec_invalid:
    #             delete_all = False
    #     if delete_all:
    #         course.delete()
    # return queryset

    day_letters = [day for day in days]
    all_days = [day for day in "MTWRFS"]
    to_remove = list(set(all_days) - set(day_letters))
    valid_sections = Section.objects.filter(course__in=list(queryset))\
        .exclude(meetings__day__in=to_remove)
    queryset = queryset.filter(sections__in=list(valid_sections))
    return queryset


def bound_filter(field):
    def filter_bounds(queryset, bounds):
        lower_bound, upper_bound = bounds.split("-")
        lower_bound = float(lower_bound)
        upper_bound = float(upper_bound)
        return queryset.filter(
            Q(**{f"{field}__gte": lower_bound, f"{field}__lte": upper_bound, })
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
            "days": day_filter
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
        ]
