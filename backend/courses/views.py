from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django_auto_prefetching import AutoPrefetchViewSetMixin
from options.models import get_value
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

import courses.examples as examples
from courses.models import Course, Requirement, Section, StatusUpdate
from courses.serializers import (
    CourseDetailSerializer,
    CourseListSerializer,
    MiniSectionSerializer,
    RequirementListSerializer,
    SectionDetailSerializer,
    StatusUpdateSerializer,
    UserSerializer,
)
from PennCourses.docs_settings import PcxAutoSchema
from plan.search import TypedSectionSearchBackend


class BaseCourseMixin(AutoPrefetchViewSetMixin, generics.GenericAPIView):
    schema = PcxAutoSchema()

    @staticmethod
    def get_semester_field():
        return "semester"

    def get_semester(self):
        semester = self.kwargs.get("semester", "current")
        if semester == "current":
            semester = get_value("SEMESTER", "all")

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
            "/api/alert/courses/": {"GET": {200: "[SCHEMA]Sections Listed Successfully."}}
        },
    )

    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all()
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
            "/api/courses/{semester}/sections/{full_code}/": {
                "GET": {200: "[SCHEMA]Section detail retrieved successfully."}
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
            "/api/courses/{semester}/courses/": {
                "GET": {200: "[SCHEMA]Courses listed successfully."}
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
                .distinct(),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course. Includes all details necessary to display course
    info, including requirements this class fulfills, and all sections.
    """

    schema = PcxAutoSchema(
        examples=examples.CourseDetail_examples,
        response_codes={
            "/api/courses/{semester}/courses/{full_code}/": {
                "GET": {200: "[SCHEMA]Courses detail retrieved successfully."}
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
                .distinct(),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class RequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of all academic requirements in the database for this semester.
    """

    schema = PcxAutoSchema(
        examples=examples.RequirementList_examples,
        response_codes={
            "/api/plan/requirements/": {"GET": {200: "[SCHEMA]Requirements listed successfully."}},
            "/api/courses/{semester}/requirements/": {
                "GET": {200: "[SCHEMA]Requirements listed successfully."}
            },
        },
    )

    serializer_class = RequirementListSerializer
    queryset = Requirement.objects.all()


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    This view exposes the Penn Labs Accounts User object.
    """

    schema = PcxAutoSchema()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user


class StatusUpdateView(generics.ListAPIView):
    """
    Retrieve all Status Update objects for a specific section.
    """

    schema = PcxAutoSchema(
        examples=examples.StatusUpdateView_examples,
        response_codes={
            "/api/courses/statusupdate/{full_code}/": {
                "GET": {200: "[SCHEMA]Status Updates for section listed successfully."}
            }
        },
        custom_path_parameter_desc={
            "/api/courses/statusupdate/{full_code}/": {
                "GET": {
                    "full_code": (
                        "The code of the section which this status update applies to, in the "
                        "form '{dept code}-{course code}-{section code}', e.g. 'CIS-120-001' for "
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
        return StatusUpdate.objects.filter(Q(section__full_code=self.kwargs["full_code"]))
