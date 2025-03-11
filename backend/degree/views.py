from collections import deque

from django.db import IntegrityError
from django.http import Http404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status, viewsets
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
    RuleSerializer,
    Rule
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
        new_degree_plan = DegreePlan(name=request.data.get("name"), person=self.request.user)
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
        

class OnboardFromTranscript(generics.ListAPIView):
    serializer_class = RuleSerializer

    def get_queryset(self):
        degree_plan_id = self.kwargs["degree_plan_id"]
        all_courses = self.kwargs["all_codes"].split(',')

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)

        # List of rule titles that should be ignored in limiting double counting
        # WITHIN a degree. Basically, only allows double counting where legal.

        # ex. CIS-1200 is allowed to fulfill the Formal Reasoning and Analysis
        # rule as well as the Computation and Cognition rule within a Cognitive Science degree.

        # ex. CIS-1200 is prevented from fulfilling both the Computation
        # rule as well as the Computation and Cognition rule within a Cognitive Science degree.

        # TODO: Remove Flexible Gen Eds once Wharton Flexible Gen Ed's is fixed.
        double_within_degree_allowed = [
            "Sector 6: The Physical World",
            "Sector 5: The Living World",
            "Sector 4: Humanities and Social Sciences",
            "Sector 3: Arts and Letters",
            "Sector 2: History and Tradition",
            "Sector 1: Society",
            "Cultural Diversity in the U.S.",
            "Cross Cultural Analysis",
            "Formal Reasoning and Analysis",
            "Quantitative Data Analysis",
            "Foreign Language",
            "Flexible Gen Eds"
        ]

        for degree in degree_plan.degrees.all():
            print(degree_plan.degrees.all())
            bfs_queue = deque()
            rules = []

            for rule_in_degree in degree.rules.all():
                bfs_queue.append(rule_in_degree)

            while len(bfs_queue):
                curr_rule = bfs_queue.pop()
                # this is a leaf rule
                if curr_rule.q:
                    rules.append(curr_rule)
                else:  # parent rule
                    bfs_queue.extend(curr_rule.children.all())

            # TODO: Only add rules that are open ended
            print(rules)


            satisfied_rules = []
            for course in all_courses:
                full_code, semester = course.split("_")
                if semester == "TRAN":
                    semester = "_TRAN"

                # print(full_code, semester)

                fulfilled_rules = set()
                curr_rules = []
                double_count_allowed_rules = []
                found_rule = False

                elective_rules = []

                for rule in rules:
                    if full_code in rule.q:
                        if rule in satisfied_rules:
                            curr_rules.append(rule.id)
                        else:
                            curr_rules = [rule.id]
                            found_rule = True

                    if rule.check_belongs([full_code]):
                        if rule.title in double_within_degree_allowed:
                            double_count_allowed_rules.append(rule.id)
                        # TODO: WORKAROUND -- Need to fix elective requirements from data dump
                        elif "elective" in rule.title.lower():
                            elective_rules.append(rule.id)
                        elif not found_rule:
                            curr_rules.append(rule.id)
                            if rule.id not in satisfied_rules:
                                f = Fulfillment.objects.all().filter(degree_plan=degree_plan).filter(rules=rule)
                                if (rule.num and len(f) >= rule.num) or (rule.credits and len(f) >= rule.credits):
                                    satisfied_rules.append(rule.id)
                                else:
                                    found_rule = True

                if len(curr_rules) != 0:
                    fulfilled_rules.update(curr_rules + double_count_allowed_rules)
                else:
                    fulfilled_rules.update(elective_rules + double_count_allowed_rules)

                for rule in fulfilled_rules:
                    f, just_created = Fulfillment.objects.get_or_create(degree_plan=degree_plan, full_code=full_code, semester=semester)
                    if just_created:
                        f.save()
                        f.rules.set(fulfilled_rules)
                    else:
                        f.rules.add(*fulfilled_rules)
                    f.save()
        
        return fulfilled_rules



class SatisfiedRuleList(generics.ListAPIView):
    """
    Provided a degree plan and a course code, retrieve a sublist
    of the degrees' rules that are satisfied by the course.
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

        rule_selected = None
        if self.kwargs["rule_id"] != "0":
            rule_selected = Rule.objects.get(id=self.kwargs["rule_id"])

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)

        # List of rule titles that should be ignored in limiting double counting
        # WITHIN a degree. Basically, only allows double counting where legal.

        # ex. CIS-1200 is allowed to fulfill the Formal Reasoning and Analysis
        # rule as well as the Computation and Cognition rule within a Cognitive Science degree.

        # ex. CIS-1200 is prevented from fulfilling both the Computation
        # rule as well as the Computation and Cognition rule within a Cognitive Science degree.

        # TODO: Remove Flexible Gen Eds once Wharton Flexible Gen Ed's is fixed.
        double_within_degree_allowed = [
            "Sector 6: The Physical World",
            "Sector 5: The Living World",
            "Sector 4: Humanities and Social Sciences",
            "Sector 3: Arts and Letters",
            "Sector 2: History and Tradition",
            "Sector 1: Society",
            "Cultural Diversity in the U.S.",
            "Cross Cultural Analysis",
            "Formal Reasoning and Analysis",
            "Quantitative Data Analysis",
            "Foreign Language",
            "Flexible Gen Eds"
        ]

        fulfilled_rules = set()

        for degree in degree_plan.degrees.all():
            bfs_queue = deque()
            rules = []

            for rule_in_degree in degree.rules.all():
                bfs_queue.append(rule_in_degree)

            while len(bfs_queue):
                curr_rule = bfs_queue.pop()
                # this is a leaf rule
                if curr_rule.q:
                    rules.append(curr_rule)
                else:  # parent rule
                    bfs_queue.extend(curr_rule.children.all())

            # TODO: Only add rules that are open ended

            curr_rules = []
            double_count_allowed_rules = []
            found_rule = False
            satisfied_rules = degree_plan.check_rules_already_satisfied(rules)

            # DIFFERENT PROCESS FOR TRANSCRIPT SCRAPING.
            if not rule_selected:
                elective_rules = []

                for rule in rules:

                    if full_code in rule.q:
                        if rule in satisfied_rules:
                            curr_rules.append(rule)
                        else:
                            curr_rules = [rule]
                            found_rule = True

                    if rule.check_belongs([full_code]):
                        if rule.title in double_within_degree_allowed:
                            double_count_allowed_rules.append(rule)
                        elif "elective" in rule.title.lower():
                            elective_rules.append(rule)
                        elif not found_rule:
                            curr_rules.append(rule)
                            if rule not in satisfied_rules:
                                found_rule = True

                if len(curr_rules) != 0:
                    fulfilled_rules.update(curr_rules + double_count_allowed_rules)
                else:
                    fulfilled_rules.update(elective_rules + double_count_allowed_rules)
            
            else:
                # PRIORITY: Check the current rule passed in.
                if rule_selected and degree.rules.all().filter(id=self.kwargs["rule_id"]) and rule_selected.check_belongs([full_code]):
                    if rule_selected.title in double_within_degree_allowed:
                        double_count_allowed_rules.append(rule_selected)
                    else:
                        curr_rules = [rule_selected]
                        found_rule = True


                for rule in rules:
                    # If an unfulfilled rule explicitly lists the provided course as an option, that
                    # should be the only course we fulfill. 

                    # If this explicit rule is fulfilled by another course, then we just add it normally.


                    # if full_code in rule.q and rule not in satified_rules:
                    if full_code in rule.q:
                        if rule in satisfied_rules:
                            curr_rules.append(rule)
                        else:
                            curr_rules = [rule]
                            found_rule = True

                    if rule.check_belongs([full_code]):
                        if rule.title in double_within_degree_allowed:
                            double_count_allowed_rules.append(rule)
                        elif not found_rule:
                            curr_rules.append(rule)
                            if rule not in satisfied_rules:
                                found_rule = True

                fulfilled_rules.update(curr_rules + double_count_allowed_rules)

        # for rule in fulfilled_rules:
        #     print(rule)
        return fulfilled_rules
    


        # bfs_queue = deque()
        # rules = []

        # for degree in degree_plan.degrees.all():
        #     for rule_in_degree in degree.rules.all():
        #         bfs_queue.append(rule_in_degree)

        # while len(bfs_queue):
        #     curr_rule = bfs_queue.pop()
        #     # this is a leaf rule
        #     if curr_rule.q:
        #         rules.append(curr_rule)
        #     else:  # parent rule
        #         bfs_queue.extend(curr_rule.children.all())

        # # TODO: Only add rules that are open ended
        # fulfilled_rules = []
        # for rule in rules:
        #     print(rule)
        #     if rule.check_belongs([full_code]):
        #         fulfilled_rules.append(rule)

        # return fulfilled_rules

