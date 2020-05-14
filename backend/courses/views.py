from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django_auto_prefetching import AutoPrefetchViewSetMixin
from options.models import get_value
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

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
from plan.search import TypedSectionSearchBackend
from django.http import HttpResponse


class BaseCourseMixin(AutoPrefetchViewSetMixin, generics.GenericAPIView):
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
    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all()
    filter_backends = [TypedSectionSearchBackend]
    search_fields = ["^full_code"]

    @staticmethod
    def get_semester_field():
        return "course__semester"


class SectionDetail(generics.RetrieveAPIView, BaseCourseMixin):
    serializer_class = SectionDetailSerializer
    queryset = Section.with_reviews.all()
    lookup_field = "full_code"

    def get_semester_field(self):
        return "course__semester"


class CourseList(generics.ListAPIView, BaseCourseMixin):
    serializer_class = CourseListSerializer
    queryset = Course.with_reviews.filter(sections__isnull=False)

    def get_queryset(self):
        queryset = Course.with_reviews.filter(sections__isnull=False)
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(meetings__isnull=False)
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct(),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Return a detailed look at a specific course. Includes all details necessary to display course
    info, including requirements this class fulfills, and all sections.
    """

    serializer_class = CourseDetailSerializer
    lookup_field = "full_code"

    def get_queryset(self):
        queryset = Course.with_reviews.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(meetings__isnull=False)
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct(),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class RequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Get a list of all requirements in the database for this semester. Includes the `id` field,
    which can be used to identify the requirement in filters.
    """

    serializer_class = RequirementListSerializer
    queryset = Requirement.objects.all()


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user


class StatusUpdateView(generics.ListAPIView):
    serializer_class = StatusUpdateSerializer
    http_method_names = ["get"]
    lookup_field = "section__full_code"

    def get_queryset(self):
        return StatusUpdate.objects.filter(Q(section__full_code=self.kwargs["full_code"]))


def open_api(request):
    data = open("openapi/openapi.yaml", "r").read()
    return HttpResponse(data, content_type="application/vnd.oai.openapi")
