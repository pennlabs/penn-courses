from rest_framework import serializers

from degree.models import DegreePlan, Rule


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = "__all__"


RuleSerializer._declared_fields["rules"] = RuleSerializer(
    many=True, read_only=True, source="children"
)


class DegreePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreePlan
        fields = "__all__"


class DegreePlanDetailSerializer(serializers.ModelSerializer):

    # field to represent the rules related to this Degree Plan
    rules = RuleSerializer(many=True, read_only=True, source="rule_set")

    class Meta:
        model = DegreePlan
        fields = "__all__"
