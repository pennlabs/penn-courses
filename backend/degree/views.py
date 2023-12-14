from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status, viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from courses.serializers import CourseListSerializer

from courses.models import Course
from degree.models import Degree, Rule, DegreePlan
from degree.utils.model_utils import q_object_parser
from degree.serializers import (
    DegreePlanDetailSerializer,
    DegreeListSerializer,
    UserDegreePlanDetailSerializer,
    UserDegreePlanListSerializer,
)
from PennCourses.docs_settings import PcxAutoSchema


class DegreeList(generics.ListAPIView):
    """
    Retrieve a list of all Degree objects.
    """

    schema = PcxAutoSchema(
        response_codes={
            "degree-list": {"GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Degrees listed successfully."}}
        },
    )

    serializer_class = DegreeListSerializer
    queryset = Degree.objects.all()


class DegreeDetail(generics.RetrieveAPIView):
    """
    Retrieve a detailed look at a specific Degree. Includes all details necessary to display degree
    info, including degree requirements that this degree needs.
    """

    schema = PcxAutoSchema(
        response_codes={
            "degree-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Degree detail retrieved successfully."}
            }
        },
    )

    serializer_class = DegreePlanDetailSerializer
    queryset = Degree.objects.all()


class UserDegreePlanViewset(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    list, retrieve, create, destroy, and update user degree plans.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DegreePlan.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            "fulfillments",
            "degree_plan",
            "degree_plan__rules",
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return UserDegreePlanListSerializer
        return UserDegreePlanDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context


@api_view(["GET"])
def rule_courses(request, rule_id: int):
    """
    Search for courses that fulfill a given rule.
    """
    try:
        rule = Rule.objects.get(id=rule_id)
    except ObjectDoesNotExist:
        return Response(
            data={"error": f"Rule with id {rule_id} does not exist."},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    q = rule.get_q_object()
    if q is None:
        return Response(
            data={"error": f"Rule with id {rule_id} has no query object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    courses = Course.objects.filter(q)
    return Response(CourseListSerializer(courses, many=True).data)
