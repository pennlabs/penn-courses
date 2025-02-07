from collections import deque
from django.db import IntegrityError
from django.http import Http404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from degree.models import Degree, DegreePlan, DockedCourse, Fulfillment, PDPBetaUser
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    DockedCourseSerializer,
    FulfillmentSerializer,
    RuleSerializer
)
from PennCourses.docs_settings import PcxAutoSchema


class InPDPBeta(BasePermission):
    def has_permission(self, request, view):
        return PDPBetaUser.objects.filter(person=request.user).exists()


class DegreeViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Degree objects.
    """

    filter_backends = [SearchFilter]
    search_fields = ["program", "degree", "concentration", "year"]
    filterset_fields = search_fields

    # After Beta: remove this permission entirely
    permission_classes = [IsAuthenticated & InPDPBeta]

    queryset = Degree.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return DegreeListSerializer
        return DegreeDetailSerializer


class DegreePlanViewset(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a DegreePlan.
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]

    def get_queryset(self):
        queryset = DegreePlan.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            "fulfillments",
            "degrees",
            "degrees__rules",
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return DegreePlanListSerializer
        else:
            return DegreePlanDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context

    def retrieve(self, request, *args, **kwargs):
        degree_plan = self.get_object()
        serializer = self.get_serializer(degree_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        if request.data.get("name") is None:
            raise ValidationError({"name": "This field is required."})
        new_degree_plan = DegreePlan(
            name=request.data.get("name"), person=self.request.user)
        new_degree_plan.save()
        serializer = self.get_serializer(new_degree_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def copy(self, request, pk=None):
        """
        Copy a degree plan.
        """
        if request.data.get("name") is None:
            raise ValidationError({"name": "This field is required."})
        degree_plan = self.get_object()
        new_degree_plan = degree_plan.copy(request.data["name"])
        serializer = self.get_serializer(new_degree_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post", "delete"])
    def degrees(self, request, pk=None):
        """
        Add or remove degrees from a degree plan.
        """
        degree_ids = request.data.get("degree_ids")
        if not isinstance(degree_ids, list):
            raise ValidationError({"degree_ids": "This field must be a list."})
        if degree_ids is None:
            raise ValidationError({"degree_ids": "This field is required."})
        degree_plan = self.get_object()

        try:
            if request.method == "POST":
                degree_plan.degrees.add(*degree_ids)
            elif request.method == "DELETE":
                degree_plan.degrees.remove(*degree_ids)
                return Response(status=status.HTTP_204_NO_CONTENT)
        except IntegrityError:
            return Response(
                data={"error": "One or more of the degrees does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(degree_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FulfillmentViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a Fulfillment.
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]
    serializer_class = FulfillmentSerializer
    http_method_names = ["get", "post", "head", "delete"]
    queryset = Fulfillment.objects.all()
    lookup_field = "full_code"

    def get_degree_plan_id(self):
        degreeplan_pk = self.kwargs["degreeplan_pk"]
        try:
            return int(degreeplan_pk)
        except (ValueError, TypeError):
            raise ValidationError("Invalid degreeplan_pk passed in URL")

    def get_queryset(self):
        queryset = Fulfillment.objects.filter(
            degree_plan__person=self.request.user,
            degree_plan_id=self.get_degree_plan_id(),
        )
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create or update fulfillment.
        """
        if request.data.get("full_code") is None:
            raise ValidationError({"full_code": "This field is required."})
        self.kwargs["full_code"] = request.data["full_code"]
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)


class DockedCourseViewset(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update docked courses
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]
    serializer_class = DockedCourseSerializer
    http_method_names = ["get", "post", "head", "delete"]
    queryset = DockedCourse.objects.all()
    lookup_field = "full_code"

    def get_queryset(self):
        queryset = DockedCourse.objects.filter(person=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        if request.data.get("full_code") is None:
            raise ValidationError({"full_code": "This field is required."})
        self.kwargs["full_code"] = request.data["full_code"]
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)


class SatisfiedRuleList(generics.ListAPIView):
    """
    Provided a degree plan and a course code, retrieve a sublist of the degrees' rules that are satisfied by the course.
    """

    schema = PcxAutoSchema(
        response_codes={
            "requirements-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Requirements listed successfully."}
            },
        },
        custom_path_parameter_desc={
            "requirements-list": {
                "GET": {
                    "semester": (
                        "The semester of the requirement (of the form YYYYx where x is A "
                        "[for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019. "
                        "We organize requirements by semester so that we don't get huge related "
                        "sets which don't give particularly good info."
                    )
                }
            }
        },
    )

    serializer_class = RuleSerializer

    def get_queryset(self):
        degree_plan_id = self.kwargs["degree_plan_id"]
        full_code = self.kwargs["full_code"]

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)


        # # List of rule titles that should be ignored in limiting double counting WITHIN a degree. Basically, only allows double counting where legal.
        # # ex. CIS-1200 is allowed to fulfill the Formal Reasoning and Analysis rule as well as the Computation and Cognition rule within a Cognitive Science degree.
        # # ex. CIS-1200 is prevented from fulfilling both the Computation rule as well as the Computation and Cognition rule within a Cognitive Science degree.
        # double_within_degree_allowed = [
        #     "Sector 6: The Physical World",
        #     "Sector 5: The Living World",
        #     "Sector 4: Humanities and Social Sciences",
        #     "Sector 3: Arts and Letters",
        #     "Sector 2: History and Tradition",
        #     "Sector 1: Society",
        #     "Cultural Diversity in the U.S.",
        #     "Cross Cultural Analysis",
        #     "Formal Reasoning and Analysis",
        #     "Quantitative Data Analysis",
        #     "Foreign Language"
        # ]

        # fulfilled_rules = []

        # for degree in degree_plan.degrees.all():
        #     bfs_queue = deque()
        #     rules = []

        #     for rule_in_degree in degree.rules.all():
        #         bfs_queue.append(rule_in_degree)

        #     while len(bfs_queue):
        #         curr_rule = bfs_queue.pop()
        #         # this is a leaf rule
        #         if curr_rule.q:
        #             rules.append(curr_rule)
        #         else:  # parent rule
        #             bfs_queue.extend(curr_rule.children.all())

        #     # TODO: Only add rules that are open ended


        #     curr_rules = []
        #     double_count_allowed_rules = []
        #     found_rule = False


        #     # print(rules)

        #     satified_rules = degree_plan.check_rules_already_satisfied(rules)
        #     for rule in rules:
                

        #         # If a rule explicitly lists the provided course as an option, that should be the onlym
        #         # course we fulfill 
        #         if full_code in rule.q and rule not in satified_rules:
        #             curr_rules = [rule]

        #         if rule.check_belongs([full_code]):
        #             if rule.title in double_within_degree_allowed:
        #                 double_count_allowed_rules.append(rule)
        #             elif not found_rule:
        #                 curr_rules.append(rule)
        #                 found_rule = True

        #     fulfilled_rules += curr_rules + double_count_allowed_rules

        # # for rule in fulfilled_rules:
        #     # print(rule)
        # return fulfilled_rules

        bfs_queue = deque()
        rules = []


        for degree in degree_plan.degrees.all():
            for rule_in_degree in degree.rules.all():
                bfs_queue.append(rule_in_degree)

        while len(bfs_queue):
            curr_rule = bfs_queue.pop()
            # this is a leaf rule
            if curr_rule.q:
                rules.append(curr_rule)
            else: # parent rule
                bfs_queue.extend(curr_rule.children.all())

        # TODO: Only add rules that are open ended
        fulfilled_rules = []
        for rule in rules:
            print(rule)
            if rule.check_belongs([full_code]):
                fulfilled_rules.append(rule)

        return fulfilled_rules
