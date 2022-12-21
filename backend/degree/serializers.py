from textwrap import dedent

from django.contrib.auth import get_user_model
from rest_framework import serializers

from degree.models import (
    DegreeRequirement,
    DegreePlan,
    Degree,
    DegreeFulfillment
)


class DegreeRequirementSerializer(serializers.ModelSerializer):
    courses = serializers.SlugRelatedField(
        slug_field='full_code',
        many=True,
        read_only=True,
    )

    class Meta:
        model = DegreeRequirement
        fields = ("id", "name", "num_courses", "num_credits", "inclusive", "courses")


class DegreeSerializer(serializers.ModelSerializer):
    requirements = DegreeRequirementSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Degree
        fields = ("id", "name", "credits", "requirements")
        read_only_fields = fields


class DegreeFulfillmentSerializer(serializers.ModelSerializer):
    requirements = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
    )

    class Meta:
        model = DegreeFulfillment
        extra_kwargs = {"override": {"required": False}} # check if want to override


class DegreePlanSerializer(serializers.ModelSerializer):
    fulfillments = DegreeFulfillmentSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = DegreePlan
        exclude = ("person",)
