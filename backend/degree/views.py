import re
from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Case, Value, When
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated
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
    PDPBetaReferral,
    PDPBetaUser,
    PDPOnboardingStatus,
    ProgramVariant,
)
from degree.serializers import (
    BetaRequestSerializer,
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    DockedCourseSerializer,
    DualProgramSerializer,
    FulfillmentSerializer,
    InviteSerializer,
    MajorDetailSerializer,
    MajorListSerializer,
    MinorDetailSerializer,
    MinorListSerializer,
    ReferralSerializer,
    Rule,
    RuleSerializer,
)
from degree.utils.composition import compose
from degree.utils.degree_logic import (
    FULFILLMENT_LEVELS,
    MIN_GRADUATE_COURSE_NUMBER,
    PlannedCourse,
    allocate_plan,
    allocate_rules,
    level_for_course,
    map_rules_and_degrees,
    prewarm_canonical_cache,
    prewarm_credits_cache,
    reconcile_rules,
    rule_subtrees,
    selection_is_legal,
    sharing_from_fulfillments,
)
from degree.utils.progress import plan_progress
from PennCourses.docs_settings import PcxAutoSchema


PENNKEY = re.compile(r"[a-z0-9]{2,16}")


class InPDPBeta(BasePermission):
    message = "Not in the PDP beta."

    def has_permission(self, request, view):
        approved = PDPBetaUser.objects.filter(
            person=request.user, status=PDPBetaUser.Status.APPROVED
        ).exists()
        if not approved and not PDPBetaReferral.redeem(request.user):
            raise PermissionDenied(self.message)
        return True


def rules_by_title_path(top_level_rules):
    """
    Every rule under the given ones, keyed by the titles from its top-level rule down. Siblings
    can share a title, so each path holds a list.
    """
    rules = {rule.id: rule for rule in rule_subtrees(top_level_rules)}

    def path(rule):
        parent = rules.get(rule.parent_id)
        return (*path(parent), rule.title) if parent else (rule.title,)

    by_path = defaultdict(list)
    for rule in rules.values():
        by_path[path(rule)].append(rule)
    return by_path


def carry_over_waivers(degree_plan, current, replacement, others):
    """
    Waive in the replacement's requirements whatever was waived in the same place in the
    current one's, matched by title, or by title and q where titles repeat. A waiver with no
    single match is dropped, unless one of the plan's `others` components still has its rule.
    """
    waived_rules = set(degree_plan.waived_rules.all())
    old = rules_by_title_path(current.rules.all())
    waived = [rule for path, rules in old.items() for rule in rules if rule in waived_rules]
    if not waived:
        return
    paths = {rule: path for path, rules in old.items() for rule in rules}
    new = rules_by_title_path(replacement.rules.all())
    kept = {rule.id for rule in rule_subtrees([r for other in others for r in other.rules.all()])}

    added = []
    for rule in waived:
        matches = new.get(paths[rule], [])
        if len(matches) > 1:
            matches = [match for match in matches if match.q == rule.q]
        if len(matches) == 1:
            added.append(matches[0])
    degree_plan.waived_rules.remove(*(rule for rule in waived if rule.id not in kept))
    degree_plan.waived_rules.add(*added)


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


def save_rule_choices(choices):
    """
    Stores the selected and unselected rules of many saved fulfillments in a few queries,
    rather than the handful each `rules.set` and `unselected_rules.set` costs per course.
    `choices` holds (fulfillment, selected, unselected) triples.
    """
    ids = [fulfillment.id for fulfillment, _, _ in choices]
    for field, index in (("rules", 1), ("unselected_rules", 2)):
        through = getattr(Fulfillment, field).through
        through.objects.filter(fulfillment_id__in=ids).delete()
        through.objects.bulk_create(
            through(fulfillment_id=choice[0].id, rule_id=rule.id)
            for choice in choices
            for rule in choice[index]
        )


def update_fulfillments(degree_plan, keep_choices=False):
    """
    Reallocates every fulfillment of a plan, which has to happen whenever the plan gains or
    loses a degree, major or minor: the rules a course can count toward, and what it may
    double count with, both change.

    With `keep_choices`, each course keeps the rules it counts for, other than waived ones,
    and only gains rules that can share with them. An override the course no longer counts for
    stays on offer, but is not chosen for it.
    """
    plan_rules = map_rules_and_degrees(degree_plan)
    waived = set(degree_plan.waived_rules.all())
    fulfillments = list(
        Fulfillment.objects.filter(degree_plan=degree_plan)
        .order_by("semester", "full_code")
        .prefetch_related("rules", "overrides")
    )
    allocations = allocate_plan(
        degree_plan,
        plan_rules,
        [
            PlannedCourse(
                fulfillment.full_code,
                is_transfer=fulfillment.is_transfer_credit,
                level=fulfillment.level,
                kept=set(fulfillment.rules.all()) - waived if keep_choices else set(),
            )
            for fulfillment in fulfillments
        ],
        waived,
    )

    for fulfillment, allocation in zip(fulfillments, allocations):
        if keep_choices:
            inactive_overrides = set(fulfillment.overrides.all()) - waived - allocation.selected
            allocation.unselected |= inactive_overrides & plan_rules.rule_to_component.keys()
        fulfillment.legal = allocation.legal

    with transaction.atomic():
        Fulfillment.objects.bulk_update(fulfillments, ["legal"])
        save_rule_choices(
            [
                (fulfillment, allocation.selected, allocation.unselected)
                for fulfillment, allocation in zip(fulfillments, allocations)
            ]
        )

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
        if self.action == "list":
            return queryset.prefetch_related(
                "degrees__rules",
                "majors__rules",
                "minors__rules",
                "fulfillments__rules",
                "waived_rules",
            )
        return queryset.prefetch_related("fulfillments", "degrees", "degrees__rules")

    def get_serializer_class(self):
        if self.action == "list":
            return DegreePlanListSerializer
        else:
            return DegreePlanDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context

    def check_plan_limit(self):
        """Call inside a transaction, before creating a plan."""
        # Locks the user's row, so two creations at once can't pass the limit together.
        get_user_model().objects.select_for_update().get(pk=self.request.user.pk)
        if DegreePlan.objects.filter(person=self.request.user).count() >= DegreePlan.MAX_PER_USER:
            raise ValidationError(
                {
                    "detail": f"You can have up to {DegreePlan.MAX_PER_USER} degree plans. "
                    "Delete one to make another."
                }
            )

    def list(self, request, *args, **kwargs):
        plans = list(self.filter_queryset(self.get_queryset()))
        context = {**self.get_serializer_context(), "progress": plan_progress(plans)}
        return Response(DegreePlanListSerializer(plans, many=True, context=context).data)

    def retrieve(self, request, *args, **kwargs):
        degree_plan = self.get_object()
        serializer = self.get_serializer(degree_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")
        if name is None:
            raise ValidationError({"name": "This field is required."})
        with transaction.atomic():
            self.check_plan_limit()
            if DegreePlan.objects.filter(name=name, person=self.request.user).exists():
                return Response(
                    {"warning": f"A degree plan with name {name} already exists."},
                    status=status.HTTP_409_CONFLICT,
                )
            new_degree_plan = DegreePlan.objects.create(name=name, person=self.request.user)
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
        with transaction.atomic():
            self.check_plan_limit()
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
        satisfied without courses and adds no course units; courses on a waived rule are
        reallocated to the requirements that remain, and overrides onto a waived rule are
        removed. Every other course keeps the requirements it counts for and its overrides.
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
                update_fulfillments(degree_plan, keep_choices=True)
            else:
                degree_plan.waived_rules.add(*ids)
                for fulfillment in degree_plan.fulfillments.filter(overrides__in=ids).distinct():
                    fulfillment.overrides.remove(*ids)
                # Reallocating can move any course, so only do it when courses must leave
                if degree_plan.fulfillments.filter(rules__in=ids).exists():
                    update_fulfillments(degree_plan, keep_choices=True)
                else:
                    degree_plan.refresh_satisfaction()
        return Response(self.get_serializer(degree_plan).data, status=status.HTTP_200_OK)

    def _check_side(self, programs, majors, degree, field):
        if programs and degree.program not in programs:
            raise ValidationError({field: f"{degree.program} is not a side of this program."})
        if majors and degree.major not in majors:
            raise ValidationError({field: f"{degree.major} is not an allowed major."})

    @action(detail=True, methods=["post"], url_path="catalog-year")
    def catalog_year(self, request, pk=None):
        """
        Switch one of the plan's degrees, majors or minors to another of its catalog years:
        `{"relation": "degrees" | "majors" | "minors", "from_id": id, "to_id": id}`. Majors and
        minors stay under the same degree, and the plan's courses are allocated afresh.
        """
        relation = request.data.get("relation")
        if relation not in ("degrees", "majors", "minors"):
            raise ValidationError({"relation": "This must be degrees, majors or minors."})
        degree_plan = self.get_object()
        placements = {"majors": DegreePlanMajor, "minors": DegreePlanMinor}
        with transaction.atomic():
            DegreePlan.objects.select_for_update().get(pk=degree_plan.pk)
            components = getattr(degree_plan, relation)
            current = components.filter(pk=request.data.get("from_id")).first()
            if current is None:
                raise ValidationError({"from_id": f"This must be one of the plan's {relation}."})
            replacement = current.catalog_years().filter(pk=request.data.get("to_id")).first()
            if replacement is None:
                raise ValidationError({"to_id": "This must be a catalog year of the same program."})
            if replacement == current:
                return Response(self.get_serializer(degree_plan).data, status=status.HTTP_200_OK)
            if components.filter(pk=replacement.pk).exists():
                raise ValidationError({"to_id": "The plan already has this catalog year."})

            others = [
                component
                for name in ("degrees", "majors", "minors")
                for component in getattr(degree_plan, name).all()
                if not (name == relation and component.pk == current.pk)
            ]
            carry_over_waivers(degree_plan, current, replacement, others)
            if relation == "degrees":
                degree_plan.degrees.remove(current)
                degree_plan.degrees.add(replacement)
                for placement in placements.values():
                    placement.objects.filter(degree_plan=degree_plan, degree=current).update(
                        degree=replacement
                    )
            else:
                field = relation[:-1]
                placements[relation].objects.filter(
                    degree_plan=degree_plan, **{field: current}
                ).update(**{field: replacement})
            update_fulfillments(degree_plan)

        return Response(self.get_serializer(degree_plan).data, status=status.HTTP_200_OK)

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
        ``unselected_rules``. It stays in the plan even if it no longer counts for anything.
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

                other.rules.set(other_selected)
                other.unselected_rules.set(other_unselected)
                other.legal = selection_is_legal(
                    other_selected, rule_to_degree, double_counts, policy
                )
                other.save()
                displaced.append({"full_code": other.full_code})

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


class BetaAccessView(APIView):
    """
    Get the user's place in the PDP beta, or ask to join it. Status is one of NONE, REQUESTED,
    APPROVED or DENIED. While PDP_BETA_REQUESTS_OPEN is off, new requests are refused.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        PDPBetaReferral.redeem(request.user)
        beta = PDPBetaUser.objects.filter(person=request.user).first()
        return Response(
            {
                "status": beta.status if beta else "NONE",
                "requests_open": settings.PDP_BETA_REQUESTS_OPEN,
            }
        )

    def post(self, request):
        if not settings.PDP_BETA_REQUESTS_OPEN:
            beta = PDPBetaUser.objects.filter(person=request.user).first()
            if beta is None:
                raise PermissionDenied("Penn Degree Plan is invite-only right now.")
            return Response({"status": beta.status})
        # Asking again changes nothing, so a denied user can't re-file by clicking again.
        beta, created = PDPBetaUser.objects.get_or_create(
            person=request.user, defaults={"status": PDPBetaUser.Status.REQUESTED}
        )
        return Response(
            {"status": beta.status},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class BetaRequestViewset(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Staff only: list the PDP beta's requests and members (filter with `?status=`), approve or
    deny one by setting its `status`, or grant a user access outright by POSTing `username`.
    """

    serializer_class = BetaRequestSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        queryset = PDPBetaUser.objects.select_related("person")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return PDPBetaUser.pending_first(queryset)

    def get_serializer_context(self):
        referrers_by_pennkey = defaultdict(list)
        for pennkey, username in PDPBetaReferral.objects.values_list(
            "pennkey", "referrer__username"
        ):
            referrers_by_pennkey[pennkey].append(username)
        return {**super().get_serializer_context(), "referrers_by_pennkey": referrers_by_pennkey}

    def perform_update(self, serializer):
        new_status = serializer.validated_data.get("status")
        if new_status is not None and new_status != serializer.instance.status:
            serializer.instance.decide(new_status)

    def create(self, request):
        username = (request.data.get("username") or "").strip()
        person = get_user_model().objects.filter(username=username).first()
        if person is None:
            raise ValidationError(
                {"username": "No one with that PennKey has logged in to Penn Courses yet."}
            )
        beta = PDPBetaUser.objects.filter(person=person).first() or PDPBetaUser(person=person)
        if beta.pk is None or beta.status != PDPBetaUser.Status.APPROVED:
            beta.decide(PDPBetaUser.Status.APPROVED)
        return Response(BetaRequestSerializer(beta).data, status=status.HTTP_201_CREATED)


class InviteView(APIView):
    """
    List the friends a beta user has invited to PDP, or invite more by POSTing `friends`, a
    list of PennKeys. Each user can invite up to three. An admin approves each invitation
    before the friend is let in and emailed.
    """

    permission_classes = [IsAuthenticated & InPDPBeta]

    def invites(self, request):
        sent = request.user.pdp_referrals.order_by("created_at")
        return {
            "invites": InviteSerializer(sent, many=True).data,
            "remaining": max(PDPBetaReferral.MAX_PER_USER - len(sent), 0),
        }

    def get(self, request):
        return Response(self.invites(request))

    def post(self, request):
        friends = request.data.get("friends")
        if not isinstance(friends, list) or not all(isinstance(f, str) for f in friends):
            raise ValidationError({"friends": "Send a list of PennKeys."})
        pennkeys = list(dict.fromkeys(f.strip().lower() for f in friends if f.strip()))
        if not pennkeys:
            raise ValidationError({"friends": "Enter at least one PennKey."})
        for pennkey in pennkeys:
            if not PENNKEY.fullmatch(pennkey):
                raise ValidationError({"friends": f"{pennkey} isn't a PennKey."})
        if request.user.username.lower() in pennkeys:
            raise ValidationError({"friends": "You can't invite yourself."})

        with transaction.atomic():
            # Locks the inviter's row, so two submissions at once can't pass the limit together.
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            already = set(request.user.pdp_referrals.values_list("pennkey", flat=True))
            new = [pennkey for pennkey in pennkeys if pennkey not in already]
            if len(already) + len(new) > PDPBetaReferral.MAX_PER_USER:
                left = max(PDPBetaReferral.MAX_PER_USER - len(already), 0)
                raise ValidationError(
                    {"friends": f"You can invite {left} more friend{'' if left == 1 else 's'}."}
                )
            PDPBetaReferral.objects.bulk_create(
                [PDPBetaReferral(referrer=request.user, pennkey=pennkey) for pennkey in new]
            )

        return Response(self.invites(request), status=status.HTTP_201_CREATED)


class ReferralViewset(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Staff only: every friend beta users have invited, pending first, with who invited them and
    the friend's beta request if they've made one. Approve or deny one by setting its `status`;
    approving lets the friend in and emails them.
    """

    serializer_class = ReferralSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        waiting = Case(When(status=PDPBetaReferral.Status.PENDING, then=Value(0)), default=Value(1))
        return (
            PDPBetaReferral.objects.select_related("referrer")
            .annotate(waiting=waiting)
            .order_by("waiting", "-created_at")
        )

    def perform_update(self, serializer):
        new_status = serializer.validated_data.get("status")
        if new_status is not None and new_status != serializer.instance.status:
            serializer.instance.decide(new_status)

    def get_serializer_context(self):
        pennkeys = set(PDPBetaReferral.objects.values_list("pennkey", flat=True))
        betas = PDPBetaUser.objects.select_related("person").filter(person__username__in=pennkeys)
        betas_by_pennkey = {beta.person.username: beta for beta in betas}
        return {**super().get_serializer_context(), "betas_by_pennkey": betas_by_pennkey}


class OnboardFromTranscript(APIView):
    """
    Given courses taken and degrees pursuing, determines an optimized assignment
    of courses to degree rules and creates relevant Fulfillment objects.
    """

    # After Beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]

    def post(self, request, degree_plan_id):
        degree_plan = get_object_or_404(DegreePlan, id=degree_plan_id, person=request.user)
        # Which transcript record each course was read off, keyed by full code. Absent for a
        # transcript with a single record, whose courses may count toward any degree.
        levels = {
            full_code: level_for_course(full_code, level)
            for full_code, level in (request.data.get("levels") or {}).items()
        }
        listed = [
            (semester["sem"], full_code)
            for semester in request.data["courses"]
            for full_code in semester["courses"]
        ]
        # A course listed twice (e.g. retaken) is stored once, as its last listing.
        last = {full_code: index for index, (_, full_code) in enumerate(listed)}
        listed = [entry for index, entry in enumerate(listed) if last[entry[1]] == index]
        # A transcript arrives in the order its courses were taken.
        allocations = allocate_plan(
            degree_plan,
            map_rules_and_degrees(degree_plan),
            [
                PlannedCourse(
                    full_code,
                    is_transfer=semester_code == TRANSFER_CREDIT_SEMESTER,
                    level=levels.get(full_code),
                )
                for semester_code, full_code in listed
            ],
            set(degree_plan.waived_rules.all()),
        )

        latest = {
            full_code: (semester_code, allocation)
            for (semester_code, full_code), allocation in zip(listed, allocations)
        }
        with transaction.atomic():
            existing = {
                fulfillment.full_code: fulfillment
                for fulfillment in Fulfillment.objects.filter(
                    degree_plan=degree_plan, full_code__in=latest
                )
            }
            choices = []
            for full_code, (semester_code, allocation) in latest.items():
                fulfillment = existing.get(full_code) or Fulfillment(
                    degree_plan=degree_plan, full_code=full_code
                )
                fulfillment.semester = semester_code
                fulfillment.legal = allocation.legal
                fulfillment.level = levels.get(full_code)
                fulfillment.from_transcript = True
                choices.append((fulfillment, allocation.selected, allocation.unselected))
            Fulfillment.objects.bulk_update(
                [f for f, _, _ in choices if f.pk],
                ["semester", "legal", "level", "from_transcript"],
            )
            Fulfillment.objects.bulk_create([f for f, _, _ in choices if not f.pk])
            save_rule_choices(choices)

        degree_plan.refresh_satisfaction()
        return Response({"message": "OK"}, status=status.HTTP_200_OK)


class SatisfiedRuleList(APIView):
    """
    Provided a degree plan and a course code, retrieve a sublist
    of the degrees' rules that are satisfied by the course.

    The optional `semester` query parameter is where the course is going. In the AP & transfer
    semester, rules that take no such credit are left out rather than offered.
    """

    # After Beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]

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
        degree_plan = get_object_or_404(DegreePlan, id=degree_plan_id, person=request.user)
        rule_selected = (
            None if kwargs["rule_id"] == "-1" else get_object_or_404(Rule, id=kwargs["rule_id"])
        )

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

        semester = request.query_params.get("semester")
        is_transfer = (
            semester == TRANSFER_CREDIT_SEMESTER
            if semester is not None
            else bool(fulfillment and fulfillment.is_transfer_credit)
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
            is_transfer=is_transfer,
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
