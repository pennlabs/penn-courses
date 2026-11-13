from collections import defaultdict
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from degree.models import (
    TRANSFER_CREDIT_SEMESTER,
    Degree,
    DegreePlan,
    DegreePlanMajor,
    DegreePlanMinor,
    DockedCourse,
    DualProgram,
    Fulfillment,
    Major,
    Minor,
    PDPBetaUser,
    PDPOnboardingStatus,
    ProgramVariant,
)
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    DockedCourseSerializer,
    DualProgramSerializer,
    FulfillmentSerializer,
    MajorDetailSerializer,
    MajorListSerializer,
    MinorDetailSerializer,
    MinorListSerializer,
    Rule,
    RuleSerializer,
)
from degree.utils.composition import compose
from degree.utils.degree_logic import (
    DEFAULT_COURSE_CREDITS,
    FULFILLMENT_LEVELS,
    MIN_GRADUATE_COURSE_NUMBER,
    CourseAllocation,
    GraduateSharing,
    allocate_rules,
    level_for_course,
    map_rules_and_degrees,
    prewarm_belongs_cache,
    prewarm_canonical_cache,
    prewarm_credits_cache,
    rebalance_allocations,
    reconcile_rules,
    rule_subtrees,
    selection_is_legal,
    sharing_from_fulfillments,
    within_policy,
)
from PennCourses.docs_settings import PcxAutoSchema


class InPDPBeta(BasePermission):
    message = "Not in the PDP beta."

    def has_permission(self, request, view):
        if not PDPBetaUser.objects.filter(person=request.user).exists():
            raise PermissionDenied(self.message)
        return True


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


def lift_waivers(degree_plan, rules):
    """A course the student puts on a waived requirement fulfills it, so its waiver is lifted."""
    lifted = list(degree_plan.waived_rules.filter(id__in=[rule.id for rule in rules]))
    if lifted:
        degree_plan.waived_rules.remove(*lifted)
        degree_plan.refresh_satisfaction()


def update_fulfillments(degree_plan):
    """
    Reallocates every fulfillment of a plan, which has to happen whenever the plan gains or
    loses a degree, major or minor: the rules a course can count toward, and what it may
    double count with, both change.
    """
    plan_rules = map_rules_and_degrees(degree_plan)
    rules_per_degree = plan_rules.rules_per_component
    rule_to_degree = plan_rules.rule_to_component
    double_counts = plan_rules.double_counts
    policy = plan_rules.composition.policy
    # Count and CU are tracked separately: a credit rule is satisfied by the sum of CUs.
    counts = defaultdict(int)
    cus = defaultdict(lambda: Decimal(0))
    # A waived requirement needs no courses, so none are allocated to it.
    waived = set(degree_plan.waived_rules.all())
    satisfied_rules = set(waived)

    def is_satisfied(rule):
        num_ok = rule.num is None or counts[rule.id] >= rule.num
        cu_ok = rule.credits is None or cus[rule.id] >= rule.credits
        return (rule.num is not None or rule.credits is not None) and num_ok and cu_ok

    fulfillments = list(
        Fulfillment.objects.filter(degree_plan=degree_plan).order_by("semester", "full_code")
    )
    # Every course is known up front, so check them against the rules in bulk
    belongs_cache = prewarm_belongs_cache(
        {rule for rules in rules_per_degree.values() for rule in rules},
        [fulfillment.full_code for fulfillment in fulfillments],
    )
    credits_cache = prewarm_credits_cache([fulfillment.full_code for fulfillment in fulfillments])
    canonical_cache = prewarm_canonical_cache(
        [fulfillment.full_code for fulfillment in fulfillments]
    )
    # Fulfillments are ordered by semester above, so the allowance goes to the earliest
    # courses eligible for it.
    graduate_sharing = GraduateSharing()
    allocations = []

    for fulfillment in fulfillments:
        selected_rules, unselected_rules, _ = allocate_rules(
            fulfillment.full_code,
            rules_per_degree,
            rule_to_degree,
            double_counts,
            degree_plan=degree_plan,
            satisfied_rules=satisfied_rules,
            belongs_cache=belongs_cache,
            is_transfer=fulfillment.is_transfer_credit,
            graduate_sharing=graduate_sharing,
            credits_cache=credits_cache,
            level=fulfillment.level,
            policy=policy,
            canonical=canonical_cache.get(fulfillment.full_code),
        )

        allocations.append(
            CourseAllocation(fulfillment.full_code, selected_rules, unselected_rules)
        )

        credits = credits_cache.get(fulfillment.full_code, DEFAULT_COURSE_CREDITS)
        for rule in selected_rules:
            counts[rule.id] += 1
            cus[rule.id] += credits
            if is_satisfied(rule):
                satisfied_rules.add(rule)

    rebalance_allocations(
        allocations,
        rule_to_degree,
        double_counts,
        credits_cache,
        allows=lambda before, after: within_policy(before, after, rule_to_degree, policy),
        exempt=waived,
    )

    with transaction.atomic():
        for fulfillment, allocation in zip(fulfillments, allocations):
            fulfillment.rules.set(allocation.selected)
            fulfillment.unselected_rules.set(allocation.unselected)
            fulfillment.legal = selection_is_legal(
                allocation.selected, rule_to_degree, double_counts, policy
            )
            fulfillment.save()

    degree_plan.refresh_satisfaction()


class MajorViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Major objects.

    These are majors as they can be added on top of a degree, carrying only their own block.
    They are not filtered by school: an Engineering student may add the major part of a College
    degree, which is what a second major is.
    """

    filter_backends = [SearchFilter]
    search_fields = ["program_code", "code", "name", "year"]
    filterset_fields = search_fields

    permission_classes = [IsAuthenticated & InPDPBeta]

    queryset = Major.objects.all()

    def get_serializer_class(self):
        return MajorListSerializer if self.action == "list" else MajorDetailSerializer


class MinorViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Minor objects.
    """

    filter_backends = [SearchFilter]
    search_fields = ["program_code", "code", "name", "year"]
    filterset_fields = search_fields

    permission_classes = [IsAuthenticated & InPDPBeta]

    queryset = Minor.objects.all()

    def get_serializer_class(self):
        return MinorListSerializer if self.action == "list" else MinorDetailSerializer


class DualProgramViewset(viewsets.ReadOnlyModelViewSet):
    """Named coordinated dual degrees: M&T, Huntsman, LSM, VIPER."""

    permission_classes = [IsAuthenticated & InPDPBeta]
    queryset = DualProgram.objects.select_related("left_variant", "right_variant")

    def get_serializer_class(self):
        return DualProgramSerializer


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
            return Response(
                {"warning": f"A degree plan with name {name} already exists."},
                status=status.HTTP_409_CONFLICT,
            )
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
        return self.update_components(request, "degrees", "degree_ids")

    @action(detail=True, methods=["post", "delete"])
    def majors(self, request, pk=None):
        """
        Add or remove majors from a degree plan. These are majors pursued beyond the one the
        plan's degree already includes, and contribute only their own block. An optional
        `degree_id` names which of the plan's degrees the majors are part of.
        """
        return self.update_components(request, "majors", "major_ids")

    @action(detail=True, methods=["post", "delete"])
    def minors(self, request, pk=None):
        """
        Add or remove minors from a degree plan. An optional `degree_id` names which of the
        plan's degrees the minors are part of.
        """
        return self.update_components(request, "minors", "minor_ids")

    @action(detail=True, methods=["post", "delete"], url_path="dual-program")
    def set_dual_program(self, request, pk=None):
        """
        Attach or clear a coordinated dual degree. Attaching adds the two sides to the plan's
        degrees, keeping the rest (a submatriculant's masters, say), and reallocates fulfillments.
        """
        degree_plan = self.get_object()
        if request.method == "DELETE":
            degree_plan.dual_program = None
            degree_plan.right_variant = None
            degree_plan.save(update_fields=["dual_program", "right_variant"])
            update_fulfillments(degree_plan)
            return Response(self.get_serializer(degree_plan).data)

        code = request.data.get("code")
        left_id = request.data.get("left_id")
        right_id = request.data.get("right_id")
        if code is None or left_id is None or right_id is None:
            raise ValidationError("code, left_id and right_id are required.")
        try:
            dual = DualProgram.objects.get(code=code)
            left = Degree.objects.get(id=left_id)
            right = Degree.objects.get(id=right_id)
        except (DualProgram.DoesNotExist, Degree.DoesNotExist):
            raise ValidationError("Unknown dual program or degree.")

        self._check_side(dual.left_programs, dual.left_allowed_majors, left, "left_id")
        self._check_side(dual.right_programs, dual.right_allowed_majors, right, "right_id")

        variant = None
        variant_code = request.data.get("right_variant")
        if variant_code:
            try:
                variant = ProgramVariant.objects.get(code=variant_code)
            except ProgramVariant.DoesNotExist:
                raise ValidationError({"right_variant": "Unknown variant."})

        with transaction.atomic():
            degree_plan.dual_program = dual
            degree_plan.right_variant = variant
            degree_plan.save(update_fields=["dual_program", "right_variant"])
            degree_plan.degrees.add(left, right)
        update_fulfillments(degree_plan)
        return Response(self.get_serializer(degree_plan).data)

    @action(detail=True, methods=["post", "delete"])
    def waivers(self, request, pk=None):
        """
        Waive requirements of a degree plan, or lift waivers, by `rule_ids`. Only individual
        requirements (leaf rules) can be waived, not whole blocks or groups. A waived rule is
        satisfied without courses and adds no course units; the plan's courses are reallocated
        to the requirements that remain, and overrides onto a waived rule are removed.
        """
        ids = request.data.get("rule_ids")
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            raise ValidationError({"rule_ids": "This field must be a list of rule ids."})

        degree_plan = self.get_object()
        # The plan's requirements as it applies them: a program like M&T replaces some of a
        # degree's requirements with its own, which are different rules.
        components = compose(degree_plan).components
        applied = {rule.id for component in components for rule in component.rules}
        roots = [
            rule for component in components for rule in (*component.roots, *component.extra_rules)
        ]
        plan_rules = {rule.id: rule for rule in rule_subtrees(roots)}
        if request.method == "POST":
            unknown = {
                i for i in ids if i not in plan_rules or (plan_rules[i].q and i not in applied)
            }
        else:
            waived = set(degree_plan.waived_rules.values_list("id", flat=True))
            unknown = set(ids) - set(plan_rules) - waived
        if unknown:
            raise ValidationError({"rule_ids": f"Not requirements of this plan: {sorted(unknown)}"})
        groups = {i for i in ids if i in plan_rules and not plan_rules[i].q}
        if request.method == "POST" and groups:
            raise ValidationError(
                {"rule_ids": f"Only individual requirements can be waived: {sorted(groups)}"}
            )

        with transaction.atomic():
            if request.method == "DELETE":
                degree_plan.waived_rules.remove(*ids)
                update_fulfillments(degree_plan)
            else:
                degree_plan.waived_rules.add(*ids)
                for fulfillment in degree_plan.fulfillments.filter(overrides__in=ids).distinct():
                    fulfillment.overrides.remove(*ids)
                # Reallocating can move any course, so only do it when courses must leave
                if degree_plan.fulfillments.filter(rules__in=ids).exists():
                    update_fulfillments(degree_plan)
                else:
                    degree_plan.refresh_satisfaction()
        return Response(self.get_serializer(degree_plan).data, status=status.HTTP_200_OK)

    def _check_side(self, programs, majors, degree, field):
        if programs and degree.program not in programs:
            raise ValidationError({field: f"{degree.program} is not a side of this program."})
        if majors and degree.major not in majors:
            raise ValidationError({field: f"{degree.major} is not an allowed major."})

    def update_components(self, request, relation, field):
        ids = request.data.get(field)
        if not isinstance(ids, list):
            raise ValidationError({field: "This field must be a list."})

        degree_plan = self.get_object()
        components = getattr(degree_plan, relation)

        placements = {"majors": DegreePlanMajor, "minors": DegreePlanMinor}
        degree_id = request.data.get("degree_id") if relation in placements else None
        if degree_id is not None and (
            not isinstance(degree_id, int) or not degree_plan.degrees.filter(pk=degree_id).exists()
        ):
            raise ValidationError({"degree_id": "This must be one of the plan's degrees."})

        try:
            # The foreign keys are deferred, so a missing id only raises when this block commits.
            with transaction.atomic():
                if request.method == "DELETE":
                    components.remove(*ids)
                    if relation == "degrees":
                        for placement in placements.values():
                            placement.objects.filter(
                                degree_plan=degree_plan, degree_id__in=ids
                            ).update(degree=None)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                components.add(*ids)
                if degree_id is not None:
                    placements[relation].objects.filter(
                        degree_plan=degree_plan, **{f"{relation[:-1]}_id__in": ids}
                    ).update(degree_id=degree_id)
                update_fulfillments(degree_plan)
        except IntegrityError:
            return Response(
                data={"error": f"One or more of the {relation} does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(self.get_serializer(degree_plan).data, status=status.HTTP_200_OK)


def list_field(data, key):
    """
    A list-valued field of a request body, or None if absent. Form-encoded bodies arrive as a
    QueryDict, whose plain `get` would return only the last value.
    """
    if key not in data:
        return None
    return data.getlist(key) if hasattr(data, "getlist") else data[key]


def set_list_field(data, key, values):
    if hasattr(data, "setlist"):
        data.setlist(key, values)
    else:
        data[key] = values


class FulfillmentViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a Fulfillment.
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]
    serializer_class = FulfillmentSerializer
    http_method_names = ["get", "post", "head", "delete"]
    queryset = Fulfillment.objects.prefetch_related("rules", "unselected_rules")
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
        ).prefetch_related("rules", "unselected_rules")
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create or update fulfillment.
        """
        if request.data.get("full_code") is None:
            raise ValidationError({"full_code": "This field is required."})
        self.kwargs["full_code"] = request.data["full_code"]

        # The client sends the rules it wants the course to count for, usually by appending
        # one to what the course already counted for. Rules that may not share are resolved
        # here, in favour of the ones just added, so what gets stored is always legal.
        request_rules = list_field(request.data, "rules")
        added = set()
        if request_rules is not None:
            degree_plan = get_object_or_404(
                DegreePlan, id=self.get_degree_plan_id(), person=request.user
            )
            plan_rules = map_rules_and_degrees(degree_plan)
            rule_to_degree = plan_rules.rule_to_component
            double_counts = plan_rules.double_counts
            rules = list(Rule.objects.filter(id__in=request_rules))
            existing = (
                Fulfillment.objects.filter(
                    degree_plan=degree_plan, full_code=request.data["full_code"]
                )
                .prefetch_related("rules", "unselected_rules")
                .first()
            )
            stored = set(existing.rules.all()) if existing else set()
            kept, demoted = reconcile_rules(
                rules,
                {rule for rule in rules if rule not in stored},
                rule_to_degree,
                double_counts,
            )
            added = set(kept) - stored

            request_unselected = list_field(request.data, "unselected_rules")
            if request_unselected is None:
                request_unselected = (
                    [rule.id for rule in existing.unselected_rules.all()] if existing else []
                )
            unselected_ids = (
                {int(rule_id) for rule_id in request_unselected} | {rule.id for rule in demoted}
            ) - {rule.id for rule in kept}

            # Make request.data mutable before modifying it
            if hasattr(request.data, "_mutable"):
                request.data._mutable = True
            set_list_field(request.data, "rules", sorted(rule.id for rule in kept))
            set_list_field(request.data, "unselected_rules", sorted(unselected_ids))
            request.data["legal"] = selection_is_legal(
                kept, rule_to_degree, double_counts, plan_rules.composition.policy
            )

        with transaction.atomic():
            try:
                response = self.partial_update(request, *args, **kwargs)
            except Http404:
                response = super().create(request, *args, **kwargs)
            if added:
                lift_waivers(degree_plan, added)
        return response

    def perform_create(self, serializer):
        serializer.save().degree_plan.refresh_satisfaction()

    def perform_update(self, serializer):
        full_code = serializer.instance.full_code
        fulfillment = serializer.save()
        if fulfillment.full_code != full_code:
            fulfillment.degree_plan.refresh_satisfaction()

    def perform_destroy(self, fulfillment):
        degree_plan = fulfillment.degree_plan
        fulfillment.delete()
        degree_plan.refresh_satisfaction()

    @action(detail=True, methods=["post"], url_path="switch-rule")
    def switch_rule(self, request, *args, **kwargs):
        """
        Switch a fulfillment's selected rule to another rule in the same degree.

        This promotes the requested rule from `unselected_rules` to `rules`, and
        demotes any currently selected rules for that same degree into
        `unselected_rules`.

        If another course was already fulfilling the target rule, that course is
        displaced: the target rule is moved from its ``rules`` to its
        ``unselected_rules``.  When the displaced course has no remaining selected
        rules its fulfillment is deleted entirely.
        """
        rule_id = request.data.get("rule_id")
        if rule_id is None:
            raise ValidationError({"rule_id": "This field is required."})

        try:
            target_rule = Rule.objects.get(id=int(rule_id))
        except (ValueError, TypeError, Rule.DoesNotExist):
            raise ValidationError({"rule_id": "Invalid rule_id."})

        fulfillment = self.get_object()
        degree_plan = fulfillment.degree_plan
        full_code = fulfillment.full_code

        plan_rules = map_rules_and_degrees(degree_plan)
        rule_to_degree = plan_rules.rule_to_component
        double_counts = plan_rules.double_counts
        policy = plan_rules.composition.policy
        if target_rule not in rule_to_degree:
            raise ValidationError({"rule_id": "Rule does not belong to this degree plan."})

        if target_rule not in fulfillment.overrides.all():
            if not target_rule.accepts(is_transfer=fulfillment.is_transfer_credit):
                raise ValidationError(
                    {"rule_id": f"Rule {target_rule.id} does not accept AP or transfer credit"}
                )
            if not target_rule.check_belongs(full_code):
                raise ValidationError(
                    {"rule_id": f"Course {full_code} does not satisfy rule {target_rule.id}"}
                )

        displaced = []

        with transaction.atomic():
            selected_rules = set(fulfillment.rules.all())
            unselected_rules = set(fulfillment.unselected_rules.all())
            if target_rule not in unselected_rules | selected_rules:
                raise ValidationError(
                    {"rule_id": "Rule is not available to switch for this fulfillment."}
                )

            target_degree = rule_to_degree[target_rule]
            selected_same_degree = {
                rule for rule in selected_rules if rule_to_degree.get(rule) == target_degree
            }

            demoted_rules = {rule for rule in selected_same_degree if rule != target_rule}
            selected_rules.difference_update(demoted_rules)
            selected_rules.add(target_rule)
            # Another component's rule may not share with the target either
            selected_rules, conflicting = reconcile_rules(
                selected_rules, {target_rule}, rule_to_degree, double_counts
            )
            demoted_rules |= conflicting
            unselected_rules.update(demoted_rules)
            unselected_rules.discard(target_rule)

            fulfillment.rules.set(selected_rules)
            fulfillment.unselected_rules.set(unselected_rules)
            fulfillment.legal = selection_is_legal(
                selected_rules, rule_to_degree, double_counts, policy
            )
            fulfillment.save()
            lift_waivers(degree_plan, [target_rule])

            other_fulfillments = (
                Fulfillment.objects.filter(
                    degree_plan=degree_plan,
                    rules=target_rule,
                )
                .exclude(full_code=full_code)
                .prefetch_related("rules", "unselected_rules")
            )

            for other in other_fulfillments:
                other_selected = set(other.rules.all())
                other_unselected = set(other.unselected_rules.all())

                other_selected.discard(target_rule)
                other_unselected.add(target_rule)

                if len(other_selected) == 0:
                    displaced.append({"full_code": other.full_code, "removed": True})
                    other.delete()
                else:
                    other.rules.set(other_selected)
                    other.unselected_rules.set(other_unselected)
                    other.legal = selection_is_legal(
                        other_selected, rule_to_degree, double_counts, policy
                    )
                    other.save()
                    displaced.append({"full_code": other.full_code, "removed": False})

            if any(entry["removed"] for entry in displaced):
                degree_plan.refresh_satisfaction()

        data = self.get_serializer(fulfillment).data
        data["displaced"] = displaced
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="level")
    def set_level(self, request, *args, **kwargs):
        """
        Marks which of a submatriculant's degrees a course is on the books for (see
        Fulfillment.level), or clears the mark with a null level, and reallocates the course's
        rules accordingly. Choices the student made that the new level still allows are kept.
        """
        if "level" not in request.data:
            raise ValidationError({"level": "This field is required."})
        level = request.data["level"] or None
        if level is not None and level not in dict(FULFILLMENT_LEVELS):
            raise ValidationError({"level": f"Must be one of {sorted(dict(FULFILLMENT_LEVELS))}."})

        fulfillment = self.get_object()
        degree_plan = fulfillment.degree_plan
        full_code = fulfillment.full_code
        if level_for_course(full_code, level) != level:
            raise ValidationError(
                {
                    "level": f"{full_code} is numbered below {MIN_GRADUATE_COURSE_NUMBER}, "
                    "so it cannot count toward a masters degree."
                }
            )

        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(degree_plan)
        others = (
            Fulfillment.objects.filter(degree_plan=degree_plan)
            .exclude(full_code=full_code)
            .prefetch_related("rules")
        )
        credits_cache = prewarm_credits_cache([f.full_code for f in others] + [full_code])
        stored = set(fulfillment.rules.all())
        selected_rules, unselected_rules, legal = allocate_rules(
            full_code,
            rules_per_degree,
            rule_to_degree,
            double_counts,
            degree_plan=degree_plan,
            is_transfer=fulfillment.is_transfer_credit,
            graduate_sharing=sharing_from_fulfillments(others, rule_to_degree, credits_cache),
            credits_cache=credits_cache,
            prior_selected=stored,
            level=level,
        )

        with transaction.atomic():
            fulfillment.level = level
            fulfillment.rules.set(selected_rules)
            fulfillment.unselected_rules.set(unselected_rules)
            fulfillment.legal = legal
            fulfillment.save()

        return Response(self.get_serializer(fulfillment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="override")
    def add_override(self, request, *args, **kwargs):
        """
        Add a manual override that allows a course to count for a rule regardless of whether
        it satisfies the rule's Q filter. Also adds the rule to the fulfillment's selected
        rules if not already present.

        POST with `{"rule_id": <id>}`.
        """
        rule_id = request.data.get("rule_id")
        if rule_id is None:
            raise ValidationError({"rule_id": "This field is required."})

        try:
            rule = Rule.objects.get(id=int(rule_id))
        except (ValueError, TypeError, Rule.DoesNotExist):
            raise ValidationError({"rule_id": "Invalid rule_id."})

        fulfillment = self.get_object()

        plan_rules = map_rules_and_degrees(fulfillment.degree_plan)
        if rule not in plan_rules.rule_to_component:
            raise ValidationError({"rule_id": "Rule does not belong to this degree plan."})

        degree_plan = fulfillment.degree_plan
        with transaction.atomic():
            fulfillment.overrides.add(rule)
            if rule not in fulfillment.rules.all():
                fulfillment.rules.add(rule)
            lift_waivers(degree_plan, [rule])

        return Response(self.get_serializer(fulfillment).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], url_path="override/(?P<rule_id>[^/.]+)")
    def remove_override(self, request, rule_id=None, *args, **kwargs):
        """
        Remove a manual override, and remove the rule from the fulfillment's selected
        and unselected rules.

        DELETE to `override/<rule_id>/`.
        """
        try:
            rule = Rule.objects.get(id=int(rule_id))
        except (ValueError, TypeError, Rule.DoesNotExist):
            raise ValidationError({"rule_id": "Invalid rule_id."})

        fulfillment = self.get_object()
        fulfillment.overrides.remove(rule)
        fulfillment.rules.remove(rule)
        fulfillment.unselected_rules.remove(rule)

        return Response(self.get_serializer(fulfillment).data, status=status.HTTP_200_OK)


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


class OnboardingStatusView(APIView):
    """
    Get or set whether the user has finished the PDP onboarding tour.
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]

    def get(self, request):
        onboarded = PDPOnboardingStatus.objects.filter(
            person=request.user, has_been_onboarded=True
        ).exists()
        return Response({"has_been_onboarded": onboarded})

    def put(self, request):
        onboarded = request.data.get("has_been_onboarded")
        if not isinstance(onboarded, bool):
            raise ValidationError({"has_been_onboarded": "Must be true or false."})
        PDPOnboardingStatus.objects.update_or_create(
            person=request.user, defaults={"has_been_onboarded": onboarded}
        )
        return Response({"has_been_onboarded": onboarded})


class OnboardFromTranscript(APIView):
    """
    Given courses taken and degrees pursuing, determines an optimized assignment
    of courses to degree rules and creates relevant Fulfillment objects.
    """

    @action(detail=True, methods=["post"])
    def post(self, request, degree_plan_id):
        counts = defaultdict(int)
        cus = defaultdict(lambda: Decimal(0))

        def is_satisfied(rule):
            num_ok = rule.num is None or counts[rule.id] >= rule.num
            cu_ok = rule.credits is None or cus[rule.id] >= rule.credits
            return (rule.num is not None or rule.credits is not None) and num_ok and cu_ok

        degree_plan = DegreePlan.objects.get(id=degree_plan_id)
        course_data = request.data["courses"]
        # Which transcript record each course was read off, keyed by full code. Absent for a
        # transcript with a single record, whose courses may count toward any degree.
        levels = {
            full_code: level_for_course(full_code, level)
            for full_code, level in (request.data.get("levels") or {}).items()
        }

        plan_rules = map_rules_and_degrees(degree_plan)
        rules_per_degree = plan_rules.rules_per_component
        rule_to_degree = plan_rules.rule_to_component
        double_counts = plan_rules.double_counts
        policy = plan_rules.composition.policy
        # A waived requirement needs no courses, so none are allocated to it.
        waived = set(degree_plan.waived_rules.all())
        satisfied_rules = set(waived)

        # Every course is known up front, so check them against the rules in bulk
        belongs_cache = prewarm_belongs_cache(
            {rule for rules in rules_per_degree.values() for rule in rules},
            [full_code for semester in course_data for full_code in semester["courses"]],
        )
        full_codes = [full_code for semester in course_data for full_code in semester["courses"]]
        credits_cache = prewarm_credits_cache(full_codes)
        canonical_cache = prewarm_canonical_cache(full_codes)
        # A transcript arrives in the order its courses were taken, so the allowance goes to
        # the earliest courses eligible for it.
        graduate_sharing = GraduateSharing()
        allocations = []

        for semester in course_data:
            for full_code in semester["courses"]:
                semester_code = semester["sem"]
                selected_rules, unselected_rules, _ = allocate_rules(
                    full_code,
                    rules_per_degree,
                    rule_to_degree,
                    double_counts,
                    degree_plan=degree_plan,
                    satisfied_rules=satisfied_rules,
                    belongs_cache=belongs_cache,
                    is_transfer=semester_code == TRANSFER_CREDIT_SEMESTER,
                    graduate_sharing=graduate_sharing,
                    credits_cache=credits_cache,
                    level=levels.get(full_code),
                    policy=policy,
                    canonical=canonical_cache.get(full_code),
                )

                allocations.append(
                    (semester_code, CourseAllocation(full_code, selected_rules, unselected_rules))
                )

                credits = credits_cache.get(full_code, DEFAULT_COURSE_CREDITS)
                for rule in selected_rules:
                    counts[rule.id] += 1
                    cus[rule.id] += credits
                    if is_satisfied(rule):
                        satisfied_rules.add(rule)

        rebalance_allocations(
            [allocation for _, allocation in allocations],
            rule_to_degree,
            double_counts,
            credits_cache,
            allows=lambda before, after: within_policy(before, after, rule_to_degree, policy),
            exempt=waived,
        )

        with transaction.atomic():
            for semester_code, allocation in allocations:
                # Keyed on Fulfillment's actual unique constraint. Including semester and
                # legal in the lookup means a course already stored with either one different
                # matches nothing and is then created against a row that already exists.
                fulfillment, _ = Fulfillment.objects.update_or_create(
                    degree_plan=degree_plan,
                    full_code=allocation.full_code,
                    defaults={
                        "semester": semester_code,
                        "legal": selection_is_legal(
                            allocation.selected, rule_to_degree, double_counts, policy
                        ),
                        "level": levels.get(allocation.full_code),
                        "from_transcript": True,
                    },
                )
                fulfillment.rules.set(allocation.selected)
                fulfillment.unselected_rules.set(allocation.unselected)

        degree_plan.refresh_satisfaction()
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

        plan_rules = map_rules_and_degrees(degree_plan)
        rules_per_degree = plan_rules.rules_per_component
        rule_to_degree = plan_rules.rule_to_component
        double_counts = plan_rules.double_counts
        policy = plan_rules.composition.policy
        # The preview has to agree with what the plan would actually grant, so the allowance
        # is charged for what the stored fulfillments already share.
        stored = list(Fulfillment.objects.filter(degree_plan=degree_plan).prefetch_related("rules"))
        credits_cache = prewarm_credits_cache([item.full_code for item in stored] + [full_code])
        canonical_cache = prewarm_canonical_cache([item.full_code for item in stored] + [full_code])
        selected_rules, unselected_rules, legal = allocate_rules(
            full_code,
            rules_per_degree,
            rule_to_degree,
            double_counts,
            rule_selected,
            degree_plan=degree_plan,
            graduate_sharing=sharing_from_fulfillments(
                [item for item in stored if item.full_code != full_code],
                rule_to_degree,
                credits_cache,
            ),
            credits_cache=credits_cache,
            policy=policy,
            canonical=canonical_cache.get(full_code),
            # A course already in the plan keeps what it counts for, so the preview adds to
            # the student's choices rather than replacing or conflicting with them.
            prior_selected=set(fulfillment.rules.all()) if fulfillment else None,
            level=fulfillment.level if fulfillment else None,
        )

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
