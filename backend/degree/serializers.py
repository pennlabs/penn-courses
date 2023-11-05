from textwrap import dedent

from django.contrib.auth import get_user_model
from rest_framework import serializers

from degree.models import DegreePlan, Rule


class RuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rule
        fields = '__all__'


class DegreePlanSerializer(serializers.ModelSerializer):
    
    # field to represent the rules related to this Degree Plan
    rules = RuleSerializer(many=True, read_only=True)

    class Meta:
        model = DegreePlan
        fields = '__all__'

