from decimal import Decimal

from django.core.exceptions import BadRequest
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.expressions import F, Subquery
from lark import Lark, Transformer, Tree
from lark.exceptions import UnexpectedInput
from rest_framework import filters

from courses.models import Course, Meeting, PreNGSSRequirement, Section
from courses.util import get_current_semester
from degree.models import Rule
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


def is_open_filter(queryset, *args):
    """
    Filters the given queryset of courses by the following condition:
    include a course only if filtering its sections by `status="O"` does
    not does not limit the set of section activities we can participate in for the course.
    In other words, include only courses for which all activities have open sections.
    Note that for compatibility, this function can take additional positional
    arguments, but these are ignored.
    """
    return queryset.filter(id__in=course_ids_by_section_query(Q(status="O")))


def day_filter(days):
    """
    Constructs a Q() query object for filtering meetings by day,
    based on the given days filter string.
    """
    days = set(days)
    if not days.issubset({"M", "T", "W", "R", "F", "S", "U"}):
        return Q()
    return Q(day__isnull=True) | Q(day__in=set(days))


def time_filter(time_range):
    """
    Constructs a Q() query object for filtering meetings by start/end time,
    based on the given time_range filter string.
    """
    if not time_range:
        return Q()
    times = time_range.split("-")
    if len(times) != 2:
        return Q()
    times = [t.strip() for t in times]
    for time in times:
        if time and not time.replace(".", "", 1).isdigit():
            return Q()
    start_time, end_time = times
    query = Q()
    if start_time:
        query &= Q(start__isnull=True) | Q(start__gte=Decimal(start_time))
    if end_time:
        query &= Q(end__isnull=True) | Q(end__lte=Decimal(end_time))
    return query


def gen_schedule_filter(request):
    """
    Generates a schedule filter function that checks for proper
    authentication in the given request.
    """

    def schedule_filter(schedule_id):
        """
        Constructs a Q() query object for filtering meetings by
        whether they fit into the specified schedule.
        """
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
        query = Q()
        for meeting in meetings:
            query &= meeting.no_conflict_query
        return query

    return schedule_filter


def pre_ngss_requirement_filter(queryset, req_ids):
    if not req_ids:
        return queryset
    query = Q()
    for req_id in req_ids.split(","):
        code, school = req_id.split("@")
        try:
            requirement = PreNGSSRequirement.objects.get(
                code=code, school=school, semester=get_current_semester()
            )
        except PreNGSSRequirement.DoesNotExist:
            continue
        query &= Q(id__in=requirement.satisfying_courses.all())

    return queryset.filter(query)


# See the attribute_filter docstring for an explanation of this grammar
# https://lark-parser.readthedocs.io/en/latest/examples/calc.html
attribute_query_parser = Lark(
    r"""
    ?expr : or_expr

    ?or_expr : and_expr
             | and_expr "|" or_expr -> disjunction

    ?and_expr : atom
              | atom "*" and_expr -> conjunction

    ?atom : attribute
          | "~" atom -> negation
          | "(" or_expr ")"

    attribute : WORD

    %import common.WORD
    %import common.WS
    %ignore WS
    """,
    start="expr",
)


class AttributeQueryTreeToCourseQ(Transformer):
    """
    Each transformation step returns a tuple of the form `(is_leaf, q)`,
    where `is_leaf` is a boolean indicating if that query expression
    is a leaf-level attribute code filter, and `q` is the query expression.
    """

    def attribute(self, children):
        (code,) = children
        return True, Q(attributes__code=code.upper())

    def disjunction(self, children):
        (c1_leaf, c1), (c2_leaf, c2) = children
        return (c1_leaf or c2_leaf), c1 | c2

    def lift_exists(self, q):
        """
        'Lifts' the given `q` query object from a leaf-level attribute
        filter (e.g. `Q(attributes__code="WUOM")`) to an 'exists' subquery,
        e.g. `Q(Exists(Course.objects.filter(attributes__code="WUOM", id=OuterRef("id"))))`.
        This is required for conjunction and negation operations, as `Q(attributes__code="WUOM")`
        simply performs a join between the `Course` and `Attribute` tables and filters the joined
        rows, so `Q(attributes__code="WUOM") & Q(attributes__code="EMCI")`
        would filter out all rows, (as no row can have code equal to both "WUOM" and "EMCI"), and
        `~Q(attributes__code="WUOM")` would filter for courses that contain some attribute
        other than WUOM (not the desired behavior). Lifing these conditions with an exists subquery
        before combining with the relevant logical connectives fixes this issue.
        """
        return Q(Exists(Course.objects.filter(q, id=OuterRef("id"))))

    def conjunction(self, children):
        children = [self.lift_exists(c) if c_leaf else c for c_leaf, c in children]
        c1, c2 = children
        return False, c1 & c2

    def negation(self, children):
        ((c_leaf, c),) = children
        if c_leaf:
            c = self.lift_exists(c)
        return False, ~c


def attribute_filter(queryset, attr_query):
    """
    :param queryset: initial Course object queryset
    :param attr_query: the attribute query string; see the description
        of the attributes query param below for an explanation of the
        syntax/semantics of this filter
    :return: filtered queryset
    """
    if not attr_query:
        return queryset

    expr = None
    try:
        expr = attribute_query_parser.parse(attr_query)
    except UnexpectedInput as e:
        raise BadRequest(e)

    def lift_demorgan(t):
        """
        Optimization: Given a Lark parse tree t, tries to
        convert `*` to leaf-level `|` operators as much as possible,
        using DeMorgan's laws (for query performance).
        """
        if t.data == "attribute":
            return t
        t.children = [lift_demorgan(c) for c in t.children]
        if t.data == "conjunction":
            c1, c2 = t.children
            if c1.data == "negation" and c2.data == "negation":
                (c1c,) = c1.children
                (c2c,) = c2.children
                return Tree(
                    data="negation",
                    children=[Tree(data="disjunction", children=[c1c, c2c])],
                )
        return t

    expr = lift_demorgan(expr)

    _, query = AttributeQueryTreeToCourseQ().transform(expr)

    return queryset.filter(query).distinct()


def bound_filter(field):
    def filter_bounds(queryset, bounds):
        if not bounds:
            return queryset
        bound_arr = bounds.split("-")
        if len(bound_arr) != 2:
            return queryset
        bound_arr = [b.strip() for b in bound_arr]
        for bound in bound_arr:
            if bound and not bound.replace(".", "", 1).isdigit():
                return queryset
        lower_bound, upper_bound = bound_arr
        lower_bound = Decimal(lower_bound)
        upper_bound = Decimal(upper_bound)

        return queryset.filter(
            Q(**{f"{field}__isnull": True})
            | Q(
                **{
                    f"{field}__gte": lower_bound,
                    f"{field}__lte": upper_bound,
                }
            )
        )

    return filter_bounds


def choice_filter(field):
    def filter_choices(queryset, choices):
        if not choices:
            return queryset
        query = Q()
        for choice in choices.split(","):
            query = query | Q(**{field: choice})

        return queryset.filter(query)

    return filter_choices


def degree_rules_filter(queryset, rule_ids):
    """
    :param queryset: initial Course object queryset
    :param rule_ids: Comma separated string of of Rule ids to filter by. If the rule does not
        have a q object, it does not filter the queryset.
    """
    if not rule_ids:
        return queryset
    query = Q()
    for rule_id in rule_ids.split(","):
        try:
            rule = Rule.objects.get(id=int(rule_id))
        except Rule.DoesNotExist | ValueError:
            continue
        q = rule.get_q_object()
        if not q:
            continue
        query &= q
    return queryset.filter(query)


class CourseSearchFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filters = {
            "attributes": attribute_filter,
            "pre_ngss_requirements": pre_ngss_requirement_filter,
            "cu": choice_filter("sections__credits"),
            "activity": choice_filter("sections__activity"),
            "course_quality": bound_filter("course_quality"),
            "instructor_quality": bound_filter("instructor_quality"),
            "difficulty": bound_filter("difficulty"),
            "is_open": is_open_filter,
            "rule_ids": degree_rules_filter,
        }
        for field, filter_func in filters.items():
            param = request.query_params.get(field)
            if param is not None:
                queryset = filter_func(queryset, param)

        # Combine meeting filter queries for efficiency
        meeting_filters = {
            "days": day_filter,
            "time": time_filter,
            "schedule-fit": gen_schedule_filter(request),
        }
        meeting_query = Q()
        for field, filter_func in meeting_filters.items():
            param = request.query_params.get(field)
            if param is not None:
                meeting_query &= filter_func(param)
        if len(meeting_query) > 0:
            queryset = meeting_filter(queryset, meeting_query)

        return queryset.distinct("full_code")  # TODO: THIS COULD BE A BREAKING CHANGE FOR PCX

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "degree_rules",
                "required": False,
                "in": "query",
                "description": (
                    "Filter to courses that satisfy certain degree Rules. Accepts "
                    "a string of comma-separated Rule ids. If multiple Rule ids "
                    "are passed then filtered courses satisfy all the rules."
                ),
                "schema": {"type": "string"},
            },
            {
                "name": "type",
                "required": False,
                "in": "query",
                "description": (
                    "Can specify what kind of query to run. Course queries are faster, "
                    "keyword queries look against professor name and course title."
                ),
                "schema": {
                    "type": "string",
                    "default": "auto",
                    "enum": ["auto", "course", "keyword"],
                },
            },
            {
                "name": "pre_ngss_requirements",
                "required": False,
                "in": "query",
                "description": (
                    "Deprecated since 2022B. Filter courses by comma-separated pre "
                    "ngss requirements, ANDed together. Use the "
                    "[List Requirements](/api/documentation/#operation/List%20Pre-Ngss%20Requirements) "  # noqa: E501
                    "endpoint to get requirement IDs."
                ),
                "schema": {"type": "string"},
                "example": "SS@SEAS,H@SEAS",
            },
            {
                "name": "attributes",
                "required": False,
                "in": "query",
                "description": (
                    "This query parameter accepts a logical expression of attribute codes "
                    "separated by `*` (AND) or `|` (OR) connectives, optionally grouped "
                    "into clauses by parentheses and arbitrarily nested (we avoid using "
                    "`&` for the AND connective so the query string doesn't have to be escaped). "
                    "You can negate an individual attribute code or a clause with the `~` operator "
                    "(this will filter for courses that do NOT have that attribute or do not "
                    "satisfy that clause). Binary operators are left-associative, "
                    "and operator precedence is as follows: `~ > * > |`. "
                    "Whitespace is ignored. "
                    "A syntax error will cause a 400 response to be returned. "
                    "Example: `(EUHS|EUSS)*(QP|QS)` would filter for courses that "
                    "satisfy the EAS humanities or social science requirements "
                    "and also have a standard grade type or a pass/fail grade type. Use the "
                    "[List Attributes](/api/documentation/#operation/List%20Attributes) endpoint "
                    "to get a list of valid attribute codes and descriptions."
                ),
                "schema": {"type": "string"},
                "example": "WUOM|WUGA",
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
                "description": (
                    "Filter meetings to be within the specified set of days. "
                    "The set of days should be specified as a string containing some "
                    "combination of the characters [M, T, W, R, F, S, U]. "
                    "This filters courses by the following condition: "
                    "include a course only if the specified day filter "
                    "does not limit the set of section activities we can participate in "
                    "for the course. "
                    "Passing an empty string will return only asynchronous classes "
                    "or classes with meeting days TBD."
                ),
                "schema": {"type": "string"},
                "example": "TWR",
            },
            {
                "name": "time",
                "required": False,
                "in": "query",
                "description": (
                    "Filter meeting times to be within the specified range. "
                    "The start and end time of the filter should be dash-separated. "
                    "Times should be specified as decimal numbers of the form `h+mm/100` "
                    "where h is the hour `[0..23]` and mm is the minute `[0,60)`, in ET. "
                    "You can omit either the start or end time to leave that side unbounded, "
                    "e.g. '11.30-'. "
                    "This filters courses by the following condition: "
                    "include a course only if the specified time filter "
                    "does not limit the set of section activities we can participate in "
                    "for the course."
                ),
                "schema": {"type": "string"},
                "example": "11.30-18",
            },
            {
                "name": "schedule-fit",
                "required": False,
                "in": "query",
                "description": (
                    "Filter meeting times to fit into the schedule with the specified integer id. "
                    "You must be authenticated with the account owning the specified schedule, "
                    "or this filter will be ignored. "
                    "This filters courses by the following condition: "
                    "include a course only if the specified schedule-fit filter "
                    "does not limit the set of section activities we can participate in "
                    "for the course."
                ),
                "schema": {"type": "integer"},
                "example": "242",
            },
            {
                "name": "is_open",
                "required": False,
                "in": "query",
                "description": (
                    "Filter courses to only those that are open. "
                    "A boolean of true should be included if you want to apply the filter. "
                    "By default (ie when the `is_open` is not supplied, the filter is not applied. "
                    "This filters courses by the following condition: "
                    "include a course only if the specification that a section is open "
                    "does not limit the set of section activities we can participate in "
                    "for the course."
                    "In other words, filter to courses for which all activities have open sections."
                ),
                "schema": {"type": "boolean"},
                "example": "true",
            },
        ]


class CourseSearchAdvancedFilterBackend(CourseSearchFilterBackend):
    def filter_queryset(self, request, queryset, view):
        pass

    def get_schema_operation_parameters(self, view):
        pass
