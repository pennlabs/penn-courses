import re

from rest_framework import filters


class TypedCourseSearchBackend(filters.SearchFilter):
    code_re = re.compile(r"^([A-Za-z]{1,4})?[ |-]?(\d{1,5})?$")

    def infer_search_type(self, query):
        if self.code_re.match(query):
            return "course"
        else:
            return "keyword"

    def get_schema_operation_parameters(self, view):
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

    @staticmethod
    def get_search_type(request):
        return request.GET.get("type", "auto")

    def get_search_terms(self, request):
        search_type = self.get_search_type(request)
        query = request.query_params.get(self.search_param, "")

        match = self.code_re.match(query)
        # If this is a course query, either by designation or by detection,
        if (
            (
                search_type == "course"
                or (search_type == "auto" and self.infer_search_type(query) == "course")
            )
            and match
            and match.group(1)
            and match.group(2)
        ):
            query = f"{match.group(1)}-{match.group(2)}"
        return [query]

    def get_search_fields(self, view, request):
        search_type = self.get_search_type(request)

        if search_type == "auto":
            search_type = self.infer_search_type(request.GET.get("search", ""))

        if search_type == "course":
            return ["^full_code"]
        elif search_type == "keyword":
            return ["title", "sections__instructors__name"]
        else:
            return super().get_search_fields(view, request)


class TypedSectionSearchBackend(filters.SearchFilter):
    code_re = re.compile(r"^([A-Za-z]+) *[ -]?(\d{3}|[A-Z]{1,3})?[ -]?(\d+)?$")

    def get_search_terms(self, request):
        query = request.query_params.get(self.search_param, "")

        match = self.code_re.match(query)
        if match:
            query = match.group(1)
            if match.group(2) is not None:
                query = query + f"-{match.group(2)}"
                if match.group(3) is not None:
                    query = query + f"-{match.group(3)}"
        return [query]
