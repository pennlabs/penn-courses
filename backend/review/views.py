from collections import Counter, defaultdict

from dateutil.tz import gettz
from django.db.models import F, Max, OuterRef, Q, Subquery, Value, Exists, Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, permission_classes, schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import (
    Course,
    Department,
    Instructor,
    NGSSRestriction,
    PreNGSSRestriction,
    Section,
    Comment
)
from courses.util import get_current_semester, get_or_create_add_drop_period, prettify_semester, get_section_from_course_instructor_semester
from PennCourses.docs_settings import PcxAutoSchema
from PennCourses.settings.base import TIME_ZONE, WAITLIST_DEPARTMENT_CODES
from review.annotations import annotate_average_and_recent, review_averages
from review.documentation import (
    ACTIVITY_CHOICES,
    autocomplete_response_schema,
    course_plots_response_schema,
    course_reviews_response_schema,
    department_reviews_response_schema,
    instructor_for_course_reviews_response_schema,
    instructor_reviews_response_schema,
)
from review.models import ALL_FIELD_SLUGS, Review
from review.util import (
    aggregate_reviews,
    avg_and_recent_demand_plots,
    avg_and_recent_percent_open_plots,
    get_average_and_recent_dict_single,
    get_num_sections,
    get_single_dict_from_qs,
    get_status_updates_map,
    make_subdict,
)
from courses.serializers import CommentSerializer, CommentListSerializer

"""
You might be wondering why these API routes are using the @api_view function decorator
from Django REST Framework rather than using any of the higher-level constructs that DRF
gives us, like Generic APIViews or ViewSets.

ViewSets define REST actions on a specific "resource" -- generally in our case, django models with
defined serializers. With these aggregations, though, there isn't a good way to define a resource
for a ViewSet to act upon. Each endpoint doesn't represent one resource, or a list of resources,
but one aggregation of all resources (ReviewBits) that fit a certain filter.

There probably is a way to fit everything into a serializer, but at the time of writing it felt like
it'd be shoe-horned in so much that it made more sense to use "bare" ApiViews.
"""


# A Q filter defining which sections we will include in demand distribution estimates,
# also used by extra_metrics_section_filters_pcr (see below)
extra_metrics_section_filters = (
    ~Q(
        course__department__code__in=WAITLIST_DEPARTMENT_CODES
    )  # Manually filter out classes from depts with waitlist systems during add/drop
    & Q(capacity__gt=0)
    & ~Q(course__semester__icontains="b")  # Filter out summer classes
    & Q(has_status_updates=True)
    & ~Q(
        id__in=Subquery(NGSSRestriction.special_approval().values("sections__id"))
    )  # Filter out sections that require permit for registration
    & ~Q(
        id__in=Subquery(PreNGSSRestriction.special_approval().values("sections__id"))
    )  # Filter out sections that require permit for registration (pre-NGSS)
)


def extra_metrics_section_filters_pcr(current_semester=None):
    """
    This function returns a Q filter for sections that should be included in
    extra PCR plots / metrics.
    """
    if current_semester is None:
        current_semester = get_current_semester()
    return extra_metrics_section_filters & Q(course__semester__lt=current_semester) & ~Q(status="X")


course_filters_pcr = ~Q(title="") | ~Q(description="") | Q(sections__has_reviews=True)
section_filters_pcr = Q(has_reviews=True) | (
    (~Q(course__title="") | ~Q(course__description="")) & ~Q(activity="REC") & ~Q(status="X")
)


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_path_parameter_desc={
            "course-reviews": {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    )
                }
            },
        },
        custom_parameters={
            "course-reviews": {
                "GET": [
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                ]
            },
        },
        override_response_schema=course_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def course_reviews(request, course_code, semester=None):
    """
    Get all reviews for the topic of a given course and other relevant information.
    Different aggregation views are provided, such as reviews spanning all semesters,
    only the most recent semester, and instructor-specific views.

    THIS SHOULD ALSO RETURN COMMENTS.
    """
    try:
        semester = request.GET.get("semester")
        course = (
            Course.objects.filter(
                course_filters_pcr,
                **(
                    {"topic__courses__full_code": course_code, "topic__courses__semester": semester}
                    if semester
                    else {"full_code": course_code}
                ),
            )
            .order_by("-semester")[:1]
            .annotate(
                branched_from_full_code=F("topic__branched_from__most_recent__full_code"),
                branched_from_semester=F("topic__branched_from__most_recent__semester"),
            )
            .select_related("topic__most_recent")
            .get()
        )
    except Course.DoesNotExist:
        raise Http404()

    topic = course.topic
    branched_from_full_code = course.branched_from_full_code
    branched_from_semester = course.branched_from_semester
    course = topic.most_recent
    course_code = course.full_code
    aliases = course.crosslistings.values_list("full_code", flat=True)

    superseded = (
        Course.objects.filter(
            course_filters_pcr,
            full_code=course_code,
        )
        .aggregate(max_semester=Max("semester"))
        .get("max_semester")
        > course.semester
        if semester
        else False
    )
    last_offered_sem_if_superceded = course.semester if superseded else None

    topic_codes = list(
        topic.courses.exclude(full_code=course.full_code)
        .values("full_code")
        .annotate(semester=Max("semester"), branched_from=Value(False))
        .values("full_code", "semester", "branched_from")
    )
    topic_branched_from = (
        {
            "full_code": branched_from_full_code,
            "semester": branched_from_semester,
            "branched_from": True,
        }
        if branched_from_full_code
        else None
    )
    historical_codes = sorted(
        topic_codes + ([topic_branched_from] if topic_branched_from else []),
        key=lambda x: x["semester"],
        reverse=True,
    )

    instructor_reviews = review_averages(
        Review.objects.filter(section__course__topic=topic),
        reviewbit_subfilters=Q(review_id=OuterRef("id")),
        section_subfilters=Q(id=OuterRef("section_id")),
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    ).annotate(instructor_name=F("instructor__name"), semester=F("section__course__semester"))
    recent_instructors = list(
        Instructor.objects.filter(
            id__in=Subquery(
                Section.objects.filter(section_filters_pcr, course__topic=topic).values(
                    "instructors__id"
                )
            )
        )
        .distinct()
        .annotate(
            most_recent_sem=Subquery(
                Section.objects.filter(instructors__id=OuterRef("id"), course__topic=topic)
                .annotate(common=Value(1))
                .values("common")
                .annotate(max_sem=Max("course__semester"))
                .values("max_sem")
            )
        )
        .values(instructor_id=F("id"), instructor_name=F("name"), semester=F("most_recent_sem"))
    )
    for instructor in recent_instructors:
        instructor["exclude_from_recent"] = True
    all_instructors = list(instructor_reviews.values()) + recent_instructors
    instructors = aggregate_reviews(all_instructors, "instructor_id", name="instructor_name")

    course_qs = annotate_average_and_recent(
        Course.objects.filter(course_filters_pcr, topic_id=topic.id).order_by("-semester")[:1],
        match_review_on=Q(section__course__topic=topic),
        match_section_on=Q(course__topic=topic) & section_filters_pcr,
        extra_metrics=True,
    )
    course = get_single_dict_from_qs(course_qs)

    num_registration_metrics = Section.objects.filter(
        extra_metrics_section_filters_pcr(),
        course__topic=topic,
    ).count()

    num_sections, num_sections_recent = get_num_sections(
        section_filters_pcr,
        course__topic=topic,
    )

    return Response(
        {
            "code": course["full_code"],
            "last_offered_sem_if_superceded": last_offered_sem_if_superceded,
            "name": course["title"],
            "description": course["description"],
            "aliases": aliases,
            "historical_codes": historical_codes,
            "latest_semester": course["semester"],
            "num_sections": num_sections,
            "num_sections_recent": num_sections_recent,
            "instructors": instructors,
            "registration_metrics": num_registration_metrics > 0,
            **get_average_and_recent_dict_single(course),
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-plots": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Plots retrieved successfully.",
                    404: "Course with given course_code not found.",
                },
            },
        },
        custom_parameters={
            "course-plots": {
                "GET": [
                    {
                        "name": "course_code",
                        "in": "path",
                        "description": "The dash-joined department and code of the course you want plots for, e.g. `CIS-120` for CIS-120.",  # noqa: E501
                        "schema": {"type": "string"},
                        "required": True,
                    },
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                    {
                        "name": "instructor_ids",
                        "in": "query",
                        "description": "A comma-separated list of instructor IDs with which to filter the sections underlying the returned plots."  # noqa: E501
                        "Note that if only invalid instructor IDs are present, plot response fields will be null or 0.",  # noqa: E501
                        "schema": {"type": "string"},
                        "required": False,
                    },
                ]
            },
        },
        override_response_schema=course_plots_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def course_plots(request, course_code):
    """
    Get all PCR plots for a given course.
    """
    try:
        semester = request.query_params.get("semester")
        course = (
            Course.objects.filter(
                course_filters_pcr,
                **(
                    {"topic__courses__full_code": course_code, "topic__courses__semester": semester}
                    if semester
                    else {"full_code": course_code}
                ),
            )
            .order_by("-semester")[:1]
            .select_related("topic__most_recent")
            .get()
        ).topic.most_recent
    except Course.DoesNotExist:
        raise Http404()

    current_semester = get_current_semester()

    # Compute set of sections to include in plot data
    filtered_sections = (
        Section.objects.filter(
            extra_metrics_section_filters_pcr(current_semester),
            course__topic_id=course.topic_id,
        )
        .annotate(efficient_semester=F("course__semester"))
        .distinct()
    )
    instructor_ids = request.GET.get("instructor_ids")
    if instructor_ids:
        instructor_ids = [int(id) for id in instructor_ids.split(",")]
        filtered_sections = filtered_sections.filter(
            instructors__id__in=instructor_ids,
        ).distinct()

    section_map = defaultdict(dict)  # a dict mapping semester to section id to section object
    for section in filtered_sections:
        section_map[section.efficient_semester][section.id] = section

    (
        avg_demand_plot,
        avg_demand_plot_min_semester,
        recent_demand_plot,
        recent_demand_plot_semester,
        avg_percent_open_plot,
        avg_percent_open_plot_min_semester,
        recent_percent_open_plot,
        recent_percent_open_plot_semester,
    ) = tuple([None] * 8)
    avg_demand_plot_num_semesters, avg_percent_open_plot_num_semesters = (0, 0)
    if section_map:
        status_updates_map = get_status_updates_map(section_map)
        (
            avg_demand_plot,
            avg_demand_plot_min_semester,
            avg_demand_plot_num_semesters,
            recent_demand_plot,
            recent_demand_plot_semester,
        ) = avg_and_recent_demand_plots(section_map, status_updates_map, bin_size=0.005)
        (
            avg_percent_open_plot,
            avg_percent_open_plot_min_semester,
            avg_percent_open_plot_num_semesters,
            recent_percent_open_plot,
            recent_percent_open_plot_semester,
        ) = avg_and_recent_percent_open_plots(section_map, status_updates_map)

    current_adp = get_or_create_add_drop_period(current_semester)
    local_tz = gettz(TIME_ZONE)

    return Response(
        {
            "code": course_code,
            "current_add_drop_period": {
                "start": current_adp.estimated_start.astimezone(tz=local_tz),
                "end": current_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": {
                "pca_demand_plot_since_semester": avg_demand_plot_min_semester,
                "pca_demand_plot_num_semesters": avg_demand_plot_num_semesters,
                "pca_demand_plot": avg_demand_plot,
                "percent_open_plot_since_semester": avg_percent_open_plot_min_semester,
                "percent_open_plot_num_semesters": avg_percent_open_plot_num_semesters,
                "percent_open_plot": avg_percent_open_plot,
            },
            "recent_plots": {
                "pca_demand_plot_since_semester": recent_demand_plot_semester,
                "pca_demand_plot_num_semesters": 1 if recent_demand_plot is not None else 0,
                "pca_demand_plot": recent_demand_plot,
                "percent_open_plot_since_semester": recent_percent_open_plot_semester,
                "percent_open_plot_num_semesters": 1 if recent_demand_plot is not None else 0,
                "percent_open_plot": recent_percent_open_plot,
            },
        }
    )


def check_instructor_id(instructor_id):
    if not isinstance(instructor_id, int) and not (
        isinstance(instructor_id, str) and instructor_id.isdigit()
    ):
        raise Http404("Instructor with given instructor_id not found.")


INSTRUCTOR_COURSE_REVIEW_FIELDS = [
    "instructor_quality",
    "course_quality",
    "work_required",
    "difficulty",
]


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "instructor-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Instructor with given instructor_id not found.",
                },
            },
        },
        custom_path_parameter_desc={
            "instructor-reviews": {
                "GET": {
                    "instructor_id": (
                        "The integer id of the instructor you want reviews for. Note that you can get the relative path for any instructor including this id by using the `url` field of objects in the `instructors` list returned by Retrieve Autocomplete Data."  # noqa E501
                    )
                }
            },
        },
        override_response_schema=instructor_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def instructor_reviews(request, instructor_id):
    """
    Get all reviews for a given instructor, aggregated by course.
    """
    check_instructor_id(instructor_id)
    instructor = get_object_or_404(Instructor, id=instructor_id)
    instructor_qs = annotate_average_and_recent(
        Instructor.objects.filter(id=instructor_id),
        match_review_on=Q(instructor_id=instructor_id),
        match_section_on=Q(instructors__id=instructor_id) & section_filters_pcr,
        extra_metrics=True,
    )
    inst = get_single_dict_from_qs(instructor_qs)

    courses = annotate_average_and_recent(
        Course.objects.filter(
            course_filters_pcr,
            sections__instructors__id=instructor_id,
        ).distinct(),
        match_review_on=Q(
            section__course__topic=OuterRef(OuterRef("topic")),
            instructor_id=instructor_id,
        ),
        match_section_on=Q(
            course__topic=OuterRef(OuterRef("topic")),
            instructors__id=instructor_id,
        ),
        extra_metrics=True,
        fields=INSTRUCTOR_COURSE_REVIEW_FIELDS,
    ).annotate(
        most_recent_full_code=F("topic__most_recent__full_code"),
    )

    num_sections, num_sections_recent = get_num_sections(
        section_filters_pcr,
        course_id__in=Subquery(
            Course.objects.filter(
                course_filters_pcr,
                sections__instructors__id=instructor_id,
            ).values("id")
        ),
    )

    # Return the most recent course taught by this instructor, for each topic
    courses_res = dict()
    max_sem = dict()
    for r in courses.values():
        if not r["average_semester_count"]:
            continue
        full_code = r["most_recent_full_code"]
        if full_code not in max_sem or max_sem[full_code] < r["semester"]:
            max_sem[full_code] = r["semester"]
            courses_res[full_code] = get_average_and_recent_dict_single(
                r, full_code="most_recent_full_code", code="most_recent_full_code", name="title"
            )

    return Response(
        {
            "name": instructor.name,
            "num_sections_recent": num_sections_recent,
            "num_sections": num_sections,
            "courses": courses_res,
            **get_average_and_recent_dict_single(inst),
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "department-reviews": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Department with the given department_code not found.",
                }
            }
        },
        custom_path_parameter_desc={
            "department-reviews": {
                "GET": {
                    "department_code": (
                        "The department code you want reviews for, e.g. `CIS` for the CIS department."  # noqa E501
                    )
                }
            },
        },
        override_response_schema=department_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def department_reviews(request, department_code):
    """
    Get reviews for all courses in a department.
    """
    department = get_object_or_404(Department, code=department_code)

    topic_id_to_course = dict()
    recent_courses = list(
        Course.objects.filter(
            course_filters_pcr,
            department=department,
        )
        .distinct()
        .values("semester", "topic_id", course_title=F("title"), course_code=F("full_code"))
    )
    for c in recent_courses:
        c["exclude_from_recent"] = True
        topic_id = c["topic_id"]
        if (
            topic_id not in topic_id_to_course
            or topic_id_to_course[topic_id]["semester"] < c["semester"]
        ):
            topic_id_to_course[topic_id] = c

    reviews = list(
        review_averages(
            Review.objects.filter(section__course__department=department),
            reviewbit_subfilters=Q(review_id=OuterRef("id")),
            section_subfilters=Q(id=OuterRef("section_id")),
            fields=ALL_FIELD_SLUGS,
            prefix="bit_",
            extra_metrics=True,
        )
        .annotate(
            topic_id=F("section__course__topic_id"),
            semester=F("section__course__semester"),
        )
        .values()
    )
    for review in reviews:
        course = topic_id_to_course[review["topic_id"]]
        review["course_code"] = course["course_code"]
        review["course_title"] = course["course_title"]

    all_courses = reviews + list(topic_id_to_course.values())
    courses = aggregate_reviews(all_courses, "course_code", code="course_code", name="course_title")

    return Response({"code": department.code, "name": department.name, "courses": courses})


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "course-history": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Reviews retrieved successfully.",
                    404: "Invalid course_code or instructor_id.",
                }
            }
        },
        custom_path_parameter_desc={
            "course-history": {
                "GET": {
                    "course_code": (
                        "The dash-joined department and code of the course you want reviews for, e.g. `CIS-120` for CIS-120."  # noqa E501
                    ),
                    "instructor_id": ("The integer id of the instructor you want reviews for."),
                }
            },
        },
        custom_parameters={
            "course-history": {
                "GET": [
                    {
                        "name": "semester",
                        "in": "query",
                        "description": "Optionally specify the semester of the desired course (defaults to most recent course with the specified course code).",  # noqa E501
                        "schema": {"type": "string"},
                        "required": False,
                    }
                ]
            },
        },
        override_response_schema=instructor_for_course_reviews_response_schema,
    )
)
@permission_classes([IsAuthenticated])
def instructor_for_course_reviews(request, course_code, instructor_id):
    """
    Get the review history of an instructor teaching a course.
    """
    try:
        semester = request.GET.get("semester")
        course = (
            Course.objects.filter(
                course_filters_pcr,
                **(
                    {"topic__courses__full_code": course_code, "topic__courses__semester": semester}
                    if semester
                    else {"full_code": course_code}
                ),
            )
            .order_by("-semester")[:1]
            .select_related("topic__most_recent")
            .get()
        )
        course = course.topic.most_recent
    except Course.DoesNotExist:
        raise Http404()

    check_instructor_id(instructor_id)
    instructor = get_object_or_404(Instructor, id=instructor_id)

    reviews = review_averages(
        Review.objects.filter(
            section__course__topic_id=course.topic_id, instructor_id=instructor_id
        ),
        reviewbit_subfilters=Q(review_id=OuterRef("id")),
        section_subfilters=Q(id=OuterRef("section_id")),
        fields=ALL_FIELD_SLUGS,
        prefix="bit_",
        extra_metrics=True,
    )
    reviews = list(
        reviews.annotate(
            course_code=F("section__course__full_code"),
            course_title=F("section__course__title"),
            activity=F("section__activity"),
            efficient_semester=F("section__course__semester"),
        ).values()
    )
    existing_sections = {r["section_id"] for r in reviews}
    all_sections = reviews + [
        s
        for s in Section.objects.filter(
            section_filters_pcr,
            course__topic_id=course.topic_id,
            instructors__id=instructor_id,
        )
        .distinct()
        .values(
            "id",
            "activity",
            course_code=F("course__full_code"),
            course_title=F("course__title"),
            efficient_semester=F("course__semester"),
        )
        if s["id"] not in existing_sections
    ]
    all_sections.sort(key=lambda s: s["efficient_semester"], reverse=True)

    return Response(
        {
            "instructor": {
                "id": instructor_id,
                "name": instructor.name,
            },
            "course_code": course.full_code,
            "sections": [
                {
                    "course_code": section["course_code"],
                    "course_name": section["course_title"],
                    "activity": ACTIVITY_CHOICES.get(section["activity"]),
                    "semester": section["efficient_semester"],
                    "forms_returned": section.get("responses"),
                    "forms_produced": section.get("enrollment"),
                    "ratings": make_subdict("bit_", section),
                    "comments": section.get("comments"),
                }
                for section in all_sections
            ],
        }
    )


@api_view(["GET"])
@schema(
    PcxAutoSchema(
        response_codes={
            "review-autocomplete": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Autocomplete dump retrieved successfully."},
            },
        },
        override_response_schema=autocomplete_response_schema,
    )
)
def autocomplete(request):
    """
    Autocomplete entries for Courses, departments, instructors. All objects have title, description,
    and url. This route does not have any path parameters or query parameters, it just dumps
    all the information necessary for frontend-based autocomplete. It is also cached
    to improve performance.
    """
    courses = (
        Course.objects.filter(course_filters_pcr)
        .annotate(
            max_semester=Subquery(
                Course.objects.filter(full_code=OuterRef("full_code"), topic=OuterRef("topic"))
                .annotate(common=Value(1))
                .values("common")
                .annotate(max_semester=Max("semester"))
                .values("max_semester")
            )
        )
        .filter(semester=F("max_semester"))
        .values("full_code", "title", "topic_id", "max_semester")
        .distinct("full_code", "topic_id")
    )
    code_counter = Counter(c["full_code"] for c in courses)
    semester_prefix = (
        lambda course: f"({prettify_semester(course['max_semester'])}) "
        if code_counter[course["full_code"]] > 1
        else ""
    )
    course_set = sorted(
        [
            {
                "title": semester_prefix(course) + course["full_code"],
                "desc": [course["title"]],
                "url": f"/course/{course['full_code']}/{course['max_semester']}",
            }
            for course in courses
        ],
        key=lambda x: x["title"],
    )
    departments = Department.objects.all().values("code", "name")
    department_set = sorted(
        [
            {
                "title": dept["code"],
                "desc": dept["name"],
                "url": f"/department/{dept['code']}",
            }
            for dept in departments
        ],
        key=lambda d: d["title"],
    )

    instructors = (
        Instructor.objects.filter(
            id__in=Subquery(Section.objects.filter(section_filters_pcr).values("instructors__id"))
        )
        .distinct()
        .values("name", "id", "section__course__department__code")
    )
    instructor_set = {}
    for inst in instructors:
        if inst["id"] not in instructor_set:
            instructor_set[inst["id"]] = {
                "title": inst["name"],
                "desc": set([inst["section__course__department__code"]]),
                "url": f"/instructor/{inst['id']}",
            }
        instructor_set[inst["id"]]["desc"].add(inst["section__course__department__code"])

    def join_depts(depts):
        try:
            return ",".join(sorted(list(depts)))
        except TypeError:
            return ""

    instructor_set = sorted(
        [
            {
                "title": v["title"],
                "desc": join_depts(v["desc"]),
                "url": v["url"],
            }
            for v in instructor_set.values()
        ],
        key=lambda x: x["title"],
    )

    return Response(
        {"courses": course_set, "departments": department_set, "instructors": instructor_set}
    )

def get_course_from_code_semester(course_code, semester):
    return (
        Course.objects.filter(
            course_filters_pcr,
            **(
                {"topic__courses__full_code": course_code, "topic__courses__semester": semester}
                if semester
                else {"full_code": course_code}
            ),
        )
        .order_by("-semester")[:1]
        .annotate(
            branched_from_full_code=F("topic__branched_from__most_recent__full_code"),
            branched_from_semester=F("topic__branched_from__most_recent__semester"),
        )
        .select_related("topic__most_recent")
        .get()
    )

# CommentsList
class CommentList(generics.ListAPIView):
    """
    Retrieve a list of all comments for the provided course.
    """

    schema = PcxAutoSchema(
        response_codes={
            "review-coursecomments": {
                "GET": {
                    200: "Course comments retrieved successfully.",
                    404: "Invalid course_code.",
                }
            },
        },
    )
    serializer_class = CommentSerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]

    def get(self, request, semester, course_code):
        semester_arg = request.query_params.get("semester") or "all"
        instructor = request.query_params.get("instructor") or "all"
        sort_by = request.query_params.get("sort_by") or "oldest"
        page = request.query_params.get("page") or 0
        page_size = request.query_params.get("page_size") or 10

        queryset = og_queryset = self.get_queryset()

        # add filters
        if semester_arg != "all":
            queryset = queryset.all().filter(semester=semester_arg)
        if instructor != "all":
            queryset = queryset.all().filter(instructor=instructor)
       
        # apply ordering
        if sort_by == "top":
            # probably not right as is at the moment – likes are marked on a per comment basis not group basis
            queryset = queryset.annotate(
                base_votes=Count("base__upvotes")-Count("base__downvotes")
            ).order_by("-base_votes", "base_id", "path")
        elif sort_by == "oldest":
            queryset = queryset.all().order_by("path")
        elif sort_by == "newest":
            queryset = queryset.all().order_by("-base_id", "path")
        
        # apply pagination (not sure how django handles OOB errors)
        user_upvotes = queryset.filter(upvotes=request.user, id=OuterRef('id'))
        user_downvotes = queryset.filter(downvotes=request.user, id=OuterRef('id'))
        queryset = queryset.annotate(
            user_upvoted=Exists(user_upvotes),
            user_downvoted=Exists(user_downvotes)
        )
        queryset = queryset.all()[page*page_size:(page+1)*page_size]

        response_body = {"comments": CommentListSerializer(queryset, many=True).data}
        if semester_arg == "all":
            response_body["semesters"] = list(og_queryset.values_list("section__course__semester", flat=True).distinct())
        
        return Response(response_body, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        course_code = self.kwargs["course_code"]
        semester = self.kwargs["semester"] or "all"
        try:
            if semester == "all":
                course = Course.objects.filter(full_code=course_code).latest("semester")
            else:
                course = get_course_from_code_semester(course_code, semester)
        except Http404:
            return Response(
                {"message": "Course not found."}, status=status.HTTP_404_NOT_FOUND
            )
        topic = course.topic
        return Comment.objects.filter(section__course__topic=topic)

# CommentViewSet
class CommentViewSet(viewsets.ModelViewSet):
    """
    get:
    Get a comment by a given `id` path parameter. If the id is not valid, a 404 is returned.

    create:
    Create a comment for the authenticated user.
    This route will return a 201 if it succeeds with a JSON in the same format as if you were
    to get the comment you just posted. If not all fields are specified (text, parent_id), a 400 is returned.

    update:
    Send a put request to this route to update / edit a specific comment.
    The `id` path parameter (an integer) specifies which comment you want to update. If a comment
    with the specified id does not exist, a 404 is returned. If a comment is not owned by the
    authenticated user, a 403 is returned. If a user edits their comment to leave a blank comment,
    a 400 is returned. Otherwise, if the request succeeds, it will return a 200 and a JSON in the 
    same format as if you were to get the comment you just posted.

    delete:
    Send a delete request to this route to delete a specific comment. The `id` path parameter
    (an integer) specifies which comment you want to update.  If a comment with the specified
    id does not exist, a 404 is returned.  If a comment is not owned by the authenticated user,
    a 403 is returned. If the delete is successful, a 204 is returned.

    Note that difference in behavior for deletion of childless comments and comments with no
    children. If a comment X has no children comments (other comments that have parent_id = comment X),
    it can be safely deleted from the database. If a comment X has children, the comment's author
    and text are wiped, but the comment stays in the database to maintain indentation and response
    logic.
    """

    request_body = {
        "id": {
            "type": "integer",
            "description": "The id of the current comment."
        },
        "text": {
            "type": "string",
            "description": "The text-content of a comment."
        },
        "parent_id": {
            "type": "integer",
            "description": "The parent id of the current comment."
        }
    }
    schema = PcxAutoSchema(
        response_codes={
            "comments-list": {
                "GET": {
                    200: "Comments listed successfully."
                }
            },
            "comments-detail": {
                "GET": {
                    200: "Comment retrieved successfully.",
                    404: "No comment with given id found."
                },
                "POST": {
                    201: "Comment created successfully.",
                    400: "Invalid parent id."
                },
                "PUT": {
                    200: "Comment updated successfully.",
                    403: "User doesn't have permission to edit comment.",
                    404: "No comment with given id found."
                },
                "DELETE": {
                    204: "Comment deleted successfully.",
                    403: "User doesn't have permission to delete this comment.",
                    404: "No comment with given id found."
                }
            }
        }
    )

    serializer_class = CommentSerializer
    http_method_names = ["get", "post", "delete", "put"]
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def retrieve(self, request, pk=None):
        comment = get_object_or_404(Comment, pk=pk)
        return Response(comment, status=status.HTTP_200_OK)
    
    def create(self, request):
        # check if comment already exists
        if Comment.objects.filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))
        
        if not all(map(lambda x: x in request.data, ["text", "course_code", "instructor", "semester"])):
            return Response(
                {"message": "Insufficient fields provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        # verify section is real
        try:
            section = get_section_from_course_instructor_semester(
                request.data.get("course_code"),
                request.data.get("instructor"),
                request.data.get("semester")
            )
        except Exception as e:
            print(e)
            return Response(
                {"message": "Section not found."}, status=status.HTTP_404_NOT_FOUND
            )
        
        # create comment and send response
        parent_id = request.data.get("parent")
        parent = get_object_or_404(Comment, pk=parent_id) if parent_id != None else None
        comment = Comment.objects.create(
            text=request.data.get("text"),
            author=request.user,
            section=section,
            parent=parent
        )
        base = parent.base if parent else comment
        prefix = parent.path + "." if parent else ""
        path = prefix + '{:0{}d}'.format(comment.id, 10)
        comment.base = base
        comment.path = path
        comment.save()

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        comment = get_object_or_404(Comment, pk=pk)

        if request.user != comment.author:
            return Response(
                {"message": "Not authorized to modify this comment."}, status=status.HTTP_403_FORBIDDEN
            )

        if "text" in request.data:
            comment.text = request.data.get("text")
            comment.save()
            return Response({"message": "Successfully edited."}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"message": "Insufficient fields presented."}, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, pk=None):
        comment = get_object_or_404(Comment, pk=pk)

        if request.user != comment.author:
            return Response(
                {"message": "Not authorized to modify this comment."}, status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
        return Response({"message": "Successfully deleted."}, status=status.HTTP_204_NO_CONTENT)
    
@api_view(["POST"])
def handle_vote(request):
    """
    Handles an incoming request that changes the vote of a comment.
    """
    if not all(map(lambda x: x in request.data, ["id", "vote_type"])):
        return Response(
            {"message": "Insufficient fields presented."}, status=status.HTTP_400_BAD_REQUEST
        )  
    
    user = request.user
    comment = get_object_or_404(Comment, pk=request.data.get("id"))
    vote_type = request.data.get("vote_type")
    if vote_type == "upvote":
        comment.downvotes.remove(user)
        comment.upvotes.add(user)
    elif vote_type == "downvote":
        comment.upvotes.remove(user)
        comment.downvotes.add(user)
    elif vote_type == "clear":
        comment.upvotes.remove(user)
        comment.downvotes.remove(user)
    
    return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def get_comment_children(request, pk):
    """
    Gets all DIRECT children for a comment.
    """
    queryset = Comment.objects.filter(parent__id=pk)
    return Response(CommentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)