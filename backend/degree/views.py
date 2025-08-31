import re
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

        # Add check for if double counting is now legal
        legal = True
        if request.data.get("rules"):
            rules = Rule.objects.all().filter(id__in=request.data.get("rules"))

            rule_to_degree = {}
            for rule in rules:
                curr_rule = rule
                while curr_rule.parent is not None:
                    curr_rule = curr_rule.parent
                rule_to_degree[rule] = curr_rule.degrees.all()[0]

            print({k.title: v.major_name for k, v in rule_to_degree.items()})

            for rule in rules:
                if any(
                    r not in rule.can_double_count_with.all()
                    and rule_to_degree[r] == rule_to_degree[rule]
                    and r != rule
                    for r in rules
                ):
                    legal = False
                    break

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


class OnboardFromTranscript(generics.ListAPIView):
    serializer_class = RuleSerializer
    """
    Primitive method for finding the rule of highest priority given a set of applicable rules.
    Currently determines priority rule by required CU count, or if the rule is explictly mentioned.
    """

    def check_dept(self, q, dept):
        pattern = r"\('([^']*)',\s*'([^']*)'\)"
        matches = re.findall(pattern, q)
        return any([match for match in matches if dept in match[1] and match[0] != "full_code"])

    def get_priority_rule(self, rules, full_code):
        priority_rule = None
        priority_tier = float("inf")
        priority_CUs = float("-inf")

        for r in rules:
            tier = None

            if full_code in r.q:
                tier = 1
            elif r.check_belongs([full_code]):
                tier = 3

            if tier is not None:
                rule_CUs = r.credits if r.credits else r.num
                if tier < priority_tier or (tier == priority_tier and rule_CUs > priority_CUs):
                    priority_rule = r
                    priority_tier = tier
                    priority_CUs = rule_CUs

        return priority_rule

    def get_queryset(self):
        satisfied_lookup = {}

        def isSatisfied(rule):
            f = satisfied_lookup[rule.id]
            return (rule.num and f >= rule.num) or (rule.credits and f >= rule.credits)

        degree_plan_id = self.kwargs["degree_plan_id"]
        all_courses = self.kwargs["all_codes"].split(",")

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)

        rules = []

        rules_per_degree = {}
        rule_to_degree = {}
        for degree in degree_plan.degrees.all():
            bfs_queue = deque()
            rules_per_degree[degree] = set()
            for rule_in_degree in degree.rules.all():
                bfs_queue.append(rule_in_degree)

            while len(bfs_queue):
                curr_rule = bfs_queue.pop()
                # this is a leaf rule
                if curr_rule.q:
                    rules.append(curr_rule)
                    rules_per_degree[degree].add(curr_rule)
                    rule_to_degree[curr_rule] = degree
                    satisfied_lookup[curr_rule.id] = 0
                else:  # parent rule
                    bfs_queue.extend(curr_rule.children.all())

        satisfied_rules = set()

        for course in all_courses:
            selected_rules = set()
            unselected_rules = set()
            legal = True

            full_code, semester = course.split("_")
            if semester == "TRAN":
                semester = "_TRAN"

            for degree in rules_per_degree:
                rules = rules_per_degree[degree].copy()

                # Find rule whose double counts we should consider.
                chosen_rule = self.get_priority_rule(rules.difference(satisfied_rules), full_code)

                # Add rules that can double count with chosen rule, and remove them from future
                # consideration.
                if chosen_rule:
                    relevant_dcrs = {
                        r
                        for r in chosen_rule.can_double_count_with.all()
                        if r.check_belongs([full_code])
                    }
                    relevant_dcrs.add(chosen_rule)

                    mutual_rules = relevant_dcrs.copy()
                    pick_one_rules = set()
                    for r1 in relevant_dcrs:
                        for r2 in relevant_dcrs:
                            if r2 not in r1.can_double_count_with.all():
                                mutual_rules.discard(r2)
                                pick_one_rules.add(r2)

                    selected_rules = selected_rules.union(mutual_rules)
                    rules.difference_update(mutual_rules)

                    if len(pick_one_rules):
                        picked_rule = (
                            chosen_rule
                            if chosen_rule in pick_one_rules
                            else self.get_priority_rule(pick_one_rules, full_code)
                        )
                        selected_rules.add(picked_rule)
                        # TODO: We use .discard() because can_double_count_with contains rules that
                        # AREN'T leaf rules. (ex. BREADTH REQUIREMENTS for Cog Sci Major). Fix!
                        rules.discard(picked_rule)

                # Consider all other rules within degree. If satisfies, add to unselected rules.
                # However, if full_code is listed and rule is currently unsatisfied, add to
                # satisfied rules (Intentionally should cause illegal double count)
                for rule in rules:
                    if full_code in rule.q and rule not in satisfied_rules:
                        selected_rules.add(rule)
                    elif rule.check_belongs([full_code]):
                        unselected_rules.add(rule)

            # Check for illegal double counting
            # TODO: Remove after testing -> obviously should produce legal assignments
            if legal:
                for rule in selected_rules:
                    if any(
                        r not in rule.can_double_count_with.all()
                        and rule_to_degree[r] == rule_to_degree[rule]
                        and r != rule
                        for r in selected_rules
                    ):
                        legal = False
                        break

            f, just_created = Fulfillment.objects.get_or_create(
                degree_plan=degree_plan, full_code=full_code, semester=semester, legal=legal
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
                if isSatisfied(rule):
                    satisfied_rules.add(rule)

        return set()


class SatisfiedRuleList(APIView):

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

    """
    Primitive method for finding the rule of highest priority given a set of applicable rules.
    Currently determines priority rule by required CU count, or if the rule is explictly mentioned.
    """

    def check_dept(self, q, dept):
        pattern = r"\('([^']*)',\s*'([^']*)'\)"
        matches = re.findall(pattern, q)
        return any([match for match in matches if dept in match[1] and match[0] != "full_code"])

    def get_priority_rule(self, rules, full_code):
        priority_rule = None
        priority_tier = float("inf")
        priority_CUs = float("-inf")

        for r in rules:
            tier = None

            if full_code in r.q:
                tier = 1
            elif r.check_belongs([full_code]):
                tier = 3

            if tier is not None:
                rule_CUs = r.credits if r.credits else r.num
                if tier < priority_tier or (tier == priority_tier and rule_CUs > priority_CUs):
                    priority_rule = r
                    priority_tier = tier
                    priority_CUs = rule_CUs

        return priority_rule

    def get(self, request, *args, **kwargs):
        degree_plan_id = kwargs["degree_plan_id"]
        full_code = kwargs["full_code"]
        print(kwargs["rule_id"])
        rule_selected = (
            None if kwargs["rule_id"] == "-1" else Rule.objects.get(id=kwargs["rule_id"])
        )

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)
        try:
            fulfillment = Fulfillment.objects.get(degree_plan=degree_plan, full_code=full_code)
        except Fulfillment.DoesNotExist:
            fulfillment = None

        print(rule_selected)
        # This shouldn't happen given frontend fixes, but just in case:
        if rule_selected and not rule_selected.check_belongs([full_code]):
            print(degree_plan_id, full_code, rule_selected)
            raise ValidationError("Course passed in doesn't fulfill rule selected!")

        selected_rules = set()
        unselected_rules = set()
        legal = True

        if fulfillment:
            selected_rules = selected_rules.union(fulfillment.rules.all())

        rule_to_degree = {}

        for degree in degree_plan.degrees.all():
            # Get leaf rules
            rules = set()
            bfs_queue = deque()
            for rule_in_degree in degree.rules.all():
                bfs_queue.append(rule_in_degree)

            while len(bfs_queue):
                curr_rule = bfs_queue.pop()
                # this is a leaf rule
                if curr_rule.q:
                    rules.add(curr_rule)
                    rule_to_degree[curr_rule] = degree
                else:  # parent rule
                    bfs_queue.extend(curr_rule.children.all())

            satisfied_rules = degree_plan.check_rules_already_satisfied(rules)

            # Find rule whose double counts we should consider.
            # If we're in the right degree, then it's rule_selected
            chosen_rule = None
            if rule_selected in rules:
                chosen_rule = rule_selected
            else:
                chosen_rule = self.get_priority_rule(rules.difference(satisfied_rules), full_code)

            # Add rules that can double count with chosen rule, and remove them from future
            # consideration.
            if chosen_rule:
                # Only double count where mutually allowed
                # Ex. Adding CIS 5550 -> area lists double count with all other area lists,
                # cis electives, tech electives, etc. However, we can't add CIS 5550 to
                # both cis electives and tech electives, and they're not mutually double
                # countable

                relevant_dcrs = {
                    r
                    for r in chosen_rule.can_double_count_with.all()
                    if r.check_belongs([full_code])
                }
                relevant_dcrs.add(chosen_rule)

                mutual_rules = relevant_dcrs.copy()
                pick_one_rules = set()
                for r1 in relevant_dcrs:
                    for r2 in relevant_dcrs:
                        if r2 not in r1.can_double_count_with.all():
                            mutual_rules.discard(r2)
                            pick_one_rules.add(r2)

                selected_rules = selected_rules.union(mutual_rules)

                rules.difference_update(mutual_rules)

                # Pick one of the pick_one_rules (if not chosen rule, it's random right now)
                if len(pick_one_rules):
                    picked_rule = (
                        chosen_rule
                        if chosen_rule in pick_one_rules
                        else self.get_priority_rule(pick_one_rules, full_code)
                    )
                    selected_rules.add(picked_rule)
                    # TODO: We use .discard() because can_double_count_with contains rules
                    # that AREN'T leaf rules. (ex. BREADTH REQUIREMENTS for Cog Sci Major). Fix!
                    rules.discard(picked_rule)

            # Consider all other rules within degree. If satisfies, add to unselected rules.
            # However, if full_code is listed and rule is currently unsatisfied, add
            # to satisfied rules (Intentionally should cause illegal double count)
            for rule in rules:
                if full_code in rule.q and rule not in satisfied_rules:
                    selected_rules.add(rule)
                elif rule.check_belongs([full_code]):
                    unselected_rules.add(rule)

        # Check for illegal double counting
        if legal:
            for rule in selected_rules:
                if any(
                    r not in rule.can_double_count_with.all()
                    and rule_to_degree[r] == rule_to_degree[rule]
                    and r != rule
                    for r in selected_rules
                ):
                    legal = False
                    break

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

        print(
            [
                rule.title
                for rule in selected_rules
                if not fulfillment or (fulfillment and rule not in fulfillment.rules.all())
            ]
        )
        print([rule.title for rule in unselected_rules])
        print(legal)

        return Response(
            {
                "selected_rules": selected_rules_to_return,
                "new_selected_rules": new_selected_rules,
                "unselected_rules": unselected_rules_to_return,
                "legal": legal,
            }
        )
