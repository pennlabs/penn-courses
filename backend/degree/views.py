from collections import defaultdict

from django.db import IntegrityError
from django.http import Http404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from degree.models import Degree, DegreePlan, DockedCourse, Fulfillment, PDPBetaUser
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    DockedCourseSerializer,
    FulfillmentSerializer,
    Rule,
    RuleSerializer,
)
from degree.utils.degree_logic import allocate_rules, check_legal, map_rules_and_degrees
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
        name = request.data.get("name")
        if name is None:
            raise ValidationError({"name": "This field is required."})
        
        if DegreePlan.objects.filter(name=name, person=self.request.user).exists():
            return Response({"warning": f"A degree plan with name {name} already exists."}, status=status.HTTP_409_CONFLICT)

        new_degree_plan = DegreePlan(name=name, person=self.request.user)
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

        # Add check for if double counting is now legal
        legal = True
        request_rules = request.data.get("rules")
        if request_rules:
            rules = Rule.objects.all().filter(id__in=request_rules)

            rule_to_degree = {}
            for rule in rules:
                curr_rule = rule
                while curr_rule.parent is not None:
                    curr_rule = curr_rule.parent
                rule_to_degree[rule] = curr_rule.degrees.first()

            legal = legal and check_legal(rules, rule_to_degree)

            # Make request.data mutable before modifying it
            if hasattr(request.data, "_mutable"):
                request.data._mutable = True
            request.data["legal"] = legal

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


class OnboardFromTranscript(APIView):
    """
    Given courses taken and degrees pursuing, determines an optimized assignment
    of courses to degree rules and creates relevant Fulfillment objects.
    """

    @action(detail=True, methods=["post"])
    def post(self, request, degree_plan_id):
        satisfied_lookup = {}

        def is_satisfied(rule):
            f = satisfied_lookup[rule.id]
            return (rule.num and f >= rule.num) or (rule.credits and f >= rule.credits)

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)
        course_data = request.data["courses"]

        satisfied_lookup = defaultdict(int)

        rules_per_degree, rule_to_degree = map_rules_and_degrees(degree_plan)
        satisfied_rules = set()
        for semester in course_data:
            for full_code in semester["courses"]:
                semester_code = semester["sem"]
                selected_rules, unselected_rules, legal = allocate_rules(
                    full_code,
                    rules_per_degree,
                    rule_to_degree,
                    degree_plan=degree_plan,
                    satisfied_rules=satisfied_rules,
                )

                f, just_created = Fulfillment.objects.get_or_create(
                    degree_plan=degree_plan,
                    full_code=full_code,
                    semester=semester_code,
                    legal=legal,
                )
                if just_created:
                    f.save()
                    f.rules.set(selected_rules)
                    f.unselected_rules.set(unselected_rules)
                else:
                    f.rules.add(selected_rules)
                    f.unselected_rules.add(unselected_rules)
                f.save()

                for rule in selected_rules:
                    satisfied_lookup[rule.id] += 1
                    if is_satisfied(rule):
                        satisfied_rules.add(rule)

        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class SatisfiedRuleList(APIView):
    """
    Provided a degree plan and a course code, retrieve a sublist
    of the degrees' rules that are satisfied by the course.
    """

    schema = PcxAutoSchema(
        response_codes={
            "satisfied-rule-list": {
                "GET": {
                    200: """Returns a list of degree requirements satisfied by the course,
                    including selected rules, newly selected rules, unselected rules that could
                    be satisfied, and whether the selections can be legally double counted."""
                }
            },
        },
        custom_path_parameter_desc={
            "satisfied-rule-list": {
                "GET": {
                    "degree_plan_id": "The ID of the degree plan to query",
                    "full_code": """The full course code (e.g., 'CIS-1200')
                                    to check against requirements""",
                    "rule_id": """The ID of a specific rule to check, or '-1'
                                to automatically determine the highest priority rule""",
                }
            }
        },
    )

    def get(self, request, *args, **kwargs):
        degree_plan_id = kwargs["degree_plan_id"]
        full_code = kwargs["full_code"]
        rule_selected = (
            None if kwargs["rule_id"] == "-1" else Rule.objects.get(id=kwargs["rule_id"])
        )

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)
        try:
            fulfillment = Fulfillment.objects.get(degree_plan=degree_plan, full_code=full_code)
        except Fulfillment.DoesNotExist:
            fulfillment = None

        # This shouldn't happen given frontend fixes, but just in case:
        if rule_selected and not rule_selected.check_belongs(full_code):
            raise ValidationError(
                f"Course passed in doesn't fulfill rule selected! "
                f"{degree_plan_id}, {full_code}, {rule_selected}"
            )

        rules_per_degree, rule_to_degree = map_rules_and_degrees(degree_plan)
        selected_rules, unselected_rules, legal = allocate_rules(
            full_code, rules_per_degree, rule_to_degree, rule_selected, degree_plan=degree_plan
        )

        if fulfillment:
            selected_rules = selected_rules.union(fulfillment.rules.all())

        # Check for illegal double counting
        legal = check_legal(selected_rules, rule_to_degree)

        selected_rules_to_return = RuleSerializer(
            Rule.objects.filter(id__in=[rule.id for rule in selected_rules]), many=True
        ).data
        new_selected_rules = RuleSerializer(
            Rule.objects.filter(
                id__in=[
                    rule.id
                    for rule in selected_rules
                    if not fulfillment or (fulfillment and rule not in fulfillment.rules.all())
                ]
            ),
            many=True,
        ).data
        unselected_rules_to_return = RuleSerializer(
            Rule.objects.filter(id__in=[rule.id for rule in unselected_rules]), many=True
        ).data

        return Response(
            {
                "selected_rules": selected_rules_to_return,
                "new_selected_rules": new_selected_rules,
                "unselected_rules": unselected_rules_to_return,
                "legal": legal,
            }
        )
