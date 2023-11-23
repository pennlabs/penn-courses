from textwrap import dedent
from rest_framework import serializers

from courses.serializers import CourseListSerializer
from courses.models import Course
from degree.models import DegreePlan, UserDegreePlan, Rule, Fulfillment, DoubleCountRestriction


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = "__all__"

# Allow recursive serialization of rules
RuleSerializer._declared_fields["rules"] = RuleSerializer(
    many=True, read_only=True, source="children"
)


class DegreePlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreePlan
        exclude = ["rules"]


class DegreePlanSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True, read_only=True)
    class Meta:
        model = DegreePlan
        fields = "__all__"


class DoubleCountRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleCountRestriction
        fields = "__all__"


class DegreePlanDetailSerializer(serializers.ModelSerializer):

    # field to represent the rules related to this Degree Plan
    rules = RuleSerializer(many=True, read_only=True)
    double_count_restrictions = DoubleCountRestrictionSerializer(many=True, read_only=True)

    class Meta:
        model = DegreePlan
        fields = "__all__"


class FulfillmentSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField(
        help=dedent(
            """
        The details of the fulfilling course. This is the most recent course with the full code, or null if no course exists with the full code.
        """
        )
    )

    def get_course(self, obj):
        course = Course.objects.filter(full_code=obj.full_code).order_by("-semester").first()
        return course and CourseListSerializer(course).data

    class Meta:
        model = Fulfillment
        fields = "__all__"


class UserDegreePlanListSerializer(serializers.ModelSerializer):
    degree_plan = DegreePlanListSerializer(read_only=True)
    id = serializers.ReadOnlyField(help_text="The id of the UserDegreePlan.")
    class Meta:
        model = UserDegreePlan
        fields = ["id", "name", "degree_plan"]


class UserDegreePlanDetailSerializer(serializers.ModelSerializer):
    fulfillments = FulfillmentSerializer(
        many=True,
        read_only=False,
        help_text="The courses used to fulfill degree plan.",
        required=True,
    )

    id = serializers.ReadOnlyField(help_text="The id of the user degree plan.")

    class Meta:
        model = UserDegreePlan
        exclude = ["person"]