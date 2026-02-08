import operator
import re
from functools import reduce

from django.db.models import Q
from rest_framework import filters


def filter_or_lookups_terms(queryset, orm_lookups, search_terms):
    """
    Filters the queryset by any of the given orm lookups matching any of the given search terms.
    """
    conditions = []
    for search_term in search_terms:
        queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
        conditions.append(reduce(operator.or_, queries))
    return queryset.filter(reduce(operator.or_, conditions))


class TypedCourseSearchBackend(filters.SearchFilter):
    code_res = [
        re.compile(r"^([A-Za-z]{" + str(dept_len) + r"})\s*-?\s*(\d{1,4}[A-Za-z]?|[A-Za-z]{1,3})?$")
        for dept_len in reversed(range(1, 5))
    ]  # To avoid ambiguity (e.g. INTL-BUL as INTLBUL), try each dept code length separately

    def get_schema_operation_parameters(self, view):
        """For autodocs."""
        return [
            {
                "name": "search",
                "schema": {"type": "string"},
                "required": False,
                "in": "query",
                "description": "Search query. Can be either a fragment of a course code, or any "
                "keyword/professor name.",
            },
        ]

    def infer_search_type(self, query):
        if not any(r.match(query) for r in self.code_res):
            return "keyword"
        else:
            return "course"

    def get_query(self, request):
        return request.GET.get(self.search_param, "").strip()

    def get_search_type(self, request):
        search_type = request.GET.get("type", "auto")
        if search_type == "auto":
            # Cache regex results for performance
            inferred_search_type = getattr(self, "inferred_search_type", None)
            search_type = inferred_search_type or self.infer_search_type(self.get_query(request))
            self.inferred_search_type = search_type
        return search_type

    def get_search_terms(self, request):
        search_type = self.get_search_type(request)
        query = self.get_query(request)

        if search_type == "keyword":
            return [query]

        def get_code_prefix(r):
            match = r.match(query)
            if match:
                components = (match.group(1), match.group(2))
                return "-".join([c for c in components if c])

        terms = [get_code_prefix(r) for r in self.code_res]
        return [t for t in terms if t]

    def get_search_fields(self, view, request):
        search_type = self.get_search_type(request)
        if search_type == "course":
            return ["^full_code"]
        else:  # keyword
            return ["title", "sections__instructors__name"]

    def filter_queryset(self, request, queryset, view):
        if not self.get_query(request):
            return queryset

        search_fields = self.get_search_fields(view, request)
        orm_lookups = [
            self.construct_search(str(search_field), queryset) for search_field in search_fields
        ]
        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset.none()

        return filter_or_lookups_terms(queryset, orm_lookups, search_terms)


class TypedSectionSearchBackend(filters.SearchFilter):
    code_res = [
        re.compile(
            r"^([A-Za-z]{" + str(dept_len) + r"})\s*-?\s*"
            r"(\d{1,4}[A-Za-z]?|[A-Za-z]{1,3})?\s*-?\s*"
            r"(\d{1,3}|[A-Za-z]{1,3})?$"
        )  # To avoid ambiguity (e.g. INTL-BUL as INTLBUL), try each dept code length separately
        for dept_len in reversed(range(1, 5))
    ]

    def get_query(self, request):
        return request.GET.get(self.search_param, "").strip()

    def get_search_terms(self, request):
        query = self.get_query(request)

        def get_code_prefix(r):
            match = r.match(query)
            if match:
                components = (match.group(1), match.group(2), match.group(3))
                return "-".join([c for c in components if c])

        terms = [get_code_prefix(r) for r in self.code_res]
        return [t for t in terms if t]

    def filter_queryset(self, request, queryset, view):
        if not self.get_query(request):
            return queryset
        orm_lookups = [self.construct_search("^full_code", queryset)]
        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset.none()

        return filter_or_lookups_terms(queryset, orm_lookups, search_terms)
