from textwrap import dedent

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


class DegreeSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True, read_only=True)

    class Meta:
        model = Degree
        fields = "__all__"


class DoubleCountRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleCountRestriction
        fields = "__all__"


class DegreeDetailSerializer(serializers.ModelSerializer):

    # Field to represent the rules related to this Degree
    rules = RuleSerializer(many=True, read_only=True)
    double_count_restrictions = DoubleCountRestrictionSerializer(many=True, read_only=True)

    class Meta:
        model = Degree
        fields = "__all__"


class FulfillmentSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField(
        help_text=dedent(
            """
            The details of the fulfilling course. This is the most recent course with the full code,
            or null if no course exists with the full code.
            """
        )
    )

    def get_course(self, obj):
        course = Course.objects.filter(full_code=obj.full_code).order_by("-semester").first()
        return course and CourseListSerializer(course).data

    class Meta:
        model = Fulfillment
        fields = "__all__"


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
