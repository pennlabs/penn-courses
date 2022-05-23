from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

import courses.examples as examples
from courses.filters import CourseSearchFilterBackend
from courses.models import Attribute, Course, PreNGSSRequirement, NGSSRestriction, Section, StatusUpdate
from courses.search import TypedCourseSearchBackend, TypedSectionSearchBackend
from courses.serializers import (
    AttributeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    MiniSectionSerializer,
    PreNGSSRequirementListSerializer,
    NGSSRestrictionListSerializer,
    SectionDetailSerializer,
    StatusUpdateSerializer,
    UserSerializer,
)
from courses.util import get_current_semester
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from plan.management.commands.recommendcourses import retrieve_course_clusters, vectorize_user


SEMESTER_PARAM_DESCRIPTION = (
    "The semester of the course (of the form YYYYx where x is A [for spring], "
    "B [summer], or C [fall]), e.g. '2019C' for fall 2019. Alternatively, you "
    "can just pass 'current' for the current semester."
)


class BaseCourseMixin(AutoPrefetchViewSetMixin, generics.GenericAPIView):
    @staticmethod
    def get_semester_field():
        return "semester"

    def get_semester(self):
        semester = self.kwargs.get("semester", "current")
        if semester == "current":
            semester = get_current_semester(allow_not_found=True)
            semester = semester if semester is not None else "all"

        return semester

    def filter_by_semester(self, queryset):
        # if we're in a view without a semester parameter, only return the current semester.
        semester = self.get_semester()
        if semester != "all":
            queryset = queryset.filter(**{self.get_semester_field(): semester})
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_semester(queryset)
        return queryset


class SectionList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of sections (less detailed than [PCx] Section, or SectionDetail on the
    backend).  The sections are filtered by the search term (assumed to be a prefix of a
    section's full code, with each chunk either space-delimited, dash-delimited, or not delimited).
    """

    schema = PcxAutoSchema(
        examples=examples.SectionList_examples,
        response_codes={
            reverse_func("section-search", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Sections Listed Successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("section-search", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all().exclude(activity="")
    filter_backends = [TypedSectionSearchBackend]
    search_fields = ["^full_code"]

    @staticmethod
    def get_semester_field():
        return "course__semester"


class SectionDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course section.
    """

    schema = PcxAutoSchema(
        examples=examples.SectionDetail_examples,
        response_codes={
            reverse_func("sections-detail", args=["semester", "full_code"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Section detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("sections-detail", args=["semester", "full_code"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = SectionDetailSerializer
    queryset = Section.with_reviews.all()
    lookup_field = "full_code"

    def get_semester_field(self):
        return "course__semester"


class CourseList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of (all) courses for the provided semester.
    """

    schema = PcxAutoSchema(
        examples=examples.CourseList_examples,
        response_codes={
            reverse_func("courses-list", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-list", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = CourseListSerializer
    queryset = Course.with_reviews.filter(sections__isnull=False)  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.filter(sections__isnull=False)
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
        queryset = self.filter_by_semester(queryset)
        return queryset


class CourseListSearch(CourseList):
    """
    This route allows you to list courses by certain search terms and/or filters.
    Without any GET parameters, this route simply returns all courses
    for a given semester. There are a few filter query parameters which constitute ranges of
    floating-point numbers. The values for these are <min>-<max> , with minimum excluded.
    For example, looking for classes in the range of 0-2.5 in difficulty, you would add the
    parameter difficulty=0-2.5. If you are a backend developer, you can find these filters in
    backend/plan/filters.py/CourseSearchFilterBackend. If you are reading the frontend docs,
    these filters are listed below in the query parameters list (with description starting with
    "Filter").
    """

    schema = PcxAutoSchema(
        examples=examples.CourseListSearch_examples,
        response_codes={
            reverse_func("courses-search", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-search", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    def get_serializer_context(self):
        """
        This method overrides the default `get_serializer_context` (from super class)
        in order to add the `user_vector` and `curr_course_vectors_dict`
        key/value pairs to the serializer context dictionary. If there is no authenticated user
        (ie `self.request.user.is_authenticated` is `False`) or `self.request` is `None`,
        the value associated with the `user_vector` and `curr_course_vectors_dict`key are not set.
        All other key/value pairs that would have been returned by the default
        `get_serializer_context` (which is `CourseList.get_serializer_context`) are in the
        dictionary returned in this method. `user_vector` and `curr_course_vectors_dict` encode the
        vectors used to calculate the recommendation score for a course for a user (see
        `backend/plan/management/commands/recommendcourses.py` for details on the vectors).
        Note that for testing purposes, this implementation of get_serializer_context is replaced
        with simply `CourseList.get_serializer_context` to reduce the costly process of training the
        model in unrelated tests. You can see how this is done and how to override that behavior in
        in `backend/tests/__init__.py`.
        """
        context = super().get_serializer_context()

        if self.request is None or not self.request.user or not self.request.user.is_authenticated:
            return context

        _, _, curr_course_vectors_dict, past_course_vectors_dict = retrieve_course_clusters()
        user_vector, _ = vectorize_user(
            self.request.user, curr_course_vectors_dict, past_course_vectors_dict
        )
        context.update(
            {"user_vector": user_vector, "curr_course_vectors_dict": curr_course_vectors_dict}
        )

        return context

    filter_backends = [TypedCourseSearchBackend, CourseSearchFilterBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course. Includes all details necessary to display course
    info, including requirements this class fulfills, and all sections.
    """

    schema = PcxAutoSchema(
        examples=examples.CourseDetail_examples,
        response_codes={
            reverse_func("courses-detail", args=["semester", "full_code"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-detail", args=["semester", "full_code"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = CourseDetailSerializer
    lookup_field = "full_code"
    queryset = Course.with_reviews.all()  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related(
                    "course", "meetings", "associated_sections", "meetings__room", "instructors"
                ),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class PreNGSSRequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of all pre-NGSS (deprecated since 2022C) academic requirements
    in the database for this semester.
    """

    schema = PcxAutoSchema(
        examples=examples.PreNGSSRequirementList_examples,
        response_codes={
            reverse_func("requirements-list", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Requirements listed successfully."}
            },
        },
        custom_path_parameter_desc={
            reverse_func("requirements-list", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = PreNGSSRequirementListSerializer
    queryset = PreNGSSRequirement.objects.all()


class AttributeList(generics.ListAPIView):
    """
    Retrieve a list of unique attributes (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        examples=examples.AttributeList_examples,
        response_codes={
            reverse_func("attributes-list"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Attributes listed successfully."}
            },
        },
    )

    serializer_class = AttributeListSerializer
    queryset = Attribute.objects.all()


class NGSSRestrictionList(generics.ListAPIView):
    """
    Retrieve a list of unique attributes (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        examples=examples.NGSSRestrictionList_examples,
        response_codes={
            reverse_func("restrictions-list"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Restrictions listed successfully."}
            },
        },
    )

    serializer_class = NGSSRestrictionListSerializer
    queryset = NGSSRestriction.objects.all()


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    This view exposes the Penn Labs Accounts User object.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user


class StatusUpdateView(generics.ListAPIView):
    """
    Retrieve all Status Update objects from the current semester for a specific section.
    """

    schema = PcxAutoSchema(
        examples=examples.StatusUpdateView_examples,
        response_codes={
            reverse_func("statusupdate", args=["full_code"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Status Updates for section listed successfully."
                }
            }
        },
        custom_path_parameter_desc={
            reverse_func("statusupdate", args=["full_code"]): {
                "GET": {
                    "full_code": (
                        "The code of the section which this status update applies to, in the "
                        "form '{dept code}-{course code}-{section code}', e.g. `CIS-120-001` for "
                        "the 001 section of CIS-120."
                    )
                }
            }
        },
    )
    serializer_class = StatusUpdateSerializer
    http_method_names = ["get"]
    lookup_field = "section__full_code"

    def get_queryset(self):
        return StatusUpdate.objects.filter(
            section__full_code=self.kwargs["full_code"],
            section__course__semester=get_current_semester(),
            in_add_drop_period=True,
        ).order_by("created_at")
