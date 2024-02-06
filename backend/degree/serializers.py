from textwrap import dedent

from django.db.models import Q
from rest_framework import serializers

from courses.models import Course
from courses.serializers import CourseListSerializer
from degree.models import Degree, DegreePlan, DoubleCountRestriction, Fulfillment, Rule

class DegreeListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Degree
        fields = "__all__"


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = "__all__"
# Allow recursive serialization of rules
RuleSerializer._declared_fields["rules"] = RuleSerializer(
    many=True, read_only=True, source="children"
)


class DoubleCountRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleCountRestriction
        fields = "__all__"

class DegreeDetailSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True, read_only=True)
    double_count_restrictions = DoubleCountRestrictionSerializer(many=True, read_only=True)

    class Meta:
        model = Degree
        fields = "__all__"

class FulfillmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(
        read_only=True,
        source="historical_course",
        help_text=dedent(
            """
            The details of the fulfilling course. This is the most recent course with the full code,
            or null if no course exists with the full code.
            """
        ),
    )
    # TODO: add a get_queryset method to only allow rules from the degree plan
    rules = serializers.PrimaryKeyRelatedField(many=True, queryset=Rule.objects.all())

    def to_internal_value(self, data):
        data = data.copy()
        data["degree_plan"] = self.context["view"].get_degree_plan_id()
        return super().to_internal_value(data)

    class Meta:
        model = Fulfillment
        fields = ["id", "degree_plan", "full_code", "course", "semester", "rules"]

    def validate(self, data):
        data = super().validate(data)
        rules = data.get("rules")  # for patch requests without a rules field
        full_code = data.get("full_code")
        degree_plan = data.get("degree_plan")

        if rules is None and full_code is None:
            return data  # Nothing to validate
        if rules is None:
            rules = self.instance.rules.all()
        if full_code is None:
            full_code = self.instance.full_code
        if degree_plan is None:
            degree_plan = self.instance.degree_plan

        # TODO: check that rules belong to this degree plan
        for rule in rules:
            if not Course.objects.filter(rule.get_q_object(), full_code=full_code).exists():
                raise serializers.ValidationError(
                    f"Course {full_code} does not satisfy rule {rule.id}"
                )

        # Check for double count restrictions
        double_count_restrictions = DoubleCountRestriction.objects.filter(
            Q(rule__in=rules) | Q(other_rule__in=rules)
        )
        for restriction in double_count_restrictions:
            if restriction.is_double_count_violated(degree_plan):
                raise serializers.ValidationError(
                    f"Double count restriction {restriction.id} violated"
                )

        return data


class DegreePlanListSerializer(serializers.ModelSerializer):
    degree = DegreeListSerializer(read_only=True)
    id = serializers.ReadOnlyField(help_text="The id of the DegreePlan.")

    class Meta:
        model = DegreePlan
        fields = ["id", "name", "degree"]


class DegreePlanDetailSerializer(serializers.ModelSerializer):
    fulfillments = FulfillmentSerializer(
        many=True,
        read_only=True,
        help_text="The courses used to fulfill degree plan.",
    )
    degree = DegreeDetailSerializer(read_only=True)
    degree_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source="degree",
        queryset=Degree.objects.all(),
        help_text="The degree_id this degree plan belongs to.",
    )
    id = serializers.ReadOnlyField(help_text="The id of the degree plan.")
    person = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DegreePlan
        fields = "__all__"
