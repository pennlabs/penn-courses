from django.core.exceptions import ObjectDoesNotExist
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from courses.models import Course
from courses.serializers import CourseListSerializer
from degree.models import Degree, DegreePlan, Fulfillment, Rule
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    FulfillmentSerializer,
)
from PennCourses.docs_settings import PcxAutoSchema


class DegreeViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Degree objects.
    """

    queryset = Degree.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["program", "degree", "concentration", "year"]
    filterset_fields = search_fields

    def get_serializer_class(self):
        if self.action == "list":
            return DegreeListSerializer
        return DegreeDetailSerializer


class DegreePlanViewset(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a DegreePlan.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DegreePlan.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            "fulfillments",
            "degree",
            "degree__rules",
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return DegreePlanListSerializer
        return DegreePlanDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context


class FulfillmentViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a Fulfillment.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FulfillmentSerializer
    queryset = Fulfillment.objects.all()

    def get_degree_plan_id(self):
        degreeplan_pk = self.kwargs["degreeplan_pk"]
        try:
            return int(degreeplan_pk)
        except ValueError | TypeError:
            raise ValidationError("Invalid degreeplan_pk passed in URL")

    def get_queryset(self):
        queryset = Fulfillment.objects.filter(
            degree_plan__person=self.request.user,
            degree_plan_id=self.get_degree_plan_id(),
        )
        return queryset


@api_view(["GET"])
def courses_for_rule(request, rule_id: int):
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
