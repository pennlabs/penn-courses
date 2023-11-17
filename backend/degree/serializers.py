from rest_framework import serializers

from degree.models import UserDegreePlan, DegreePlan, Rule
from courses.serializers import CourseDetailSerializer

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = "__all__"


RuleSerializer._declared_fields["rules"] = RuleSerializer(
    many=True, read_only=True, source="children"
)


class DegreePlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreePlan
        fields = "__all__"


class DegreePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreePlan
        fields = "__all__"


class DegreePlanDetailSerializer(serializers.ModelSerializer):

    # field to represent the rules related to this Degree Plan
    rules = RuleSerializer(many=True, read_only=True, source="rule_set", source="rule_set")

    class Meta:
        model = DegreePlan
        fields = "__all__"


class UserDegreePlanSerializer(serializers.ModelSerializer):
    courses = CourseDetailSerializer(
        many=True,
        read_only=False,
        help_text="The courses used to fulfill degree plan.",
        required=True,
    )

    id = serializers.ReadOnlyField(help_text="The id of the schedule.")

    class Meta:
        model = UserDegreePlan
        exclude = ["person"]