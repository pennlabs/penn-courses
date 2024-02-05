from django.core.exceptions import ObjectDoesNotExist
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

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

    serializer_class = DegreeDetailSerializer
    queryset = Degree.objects.all()


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
