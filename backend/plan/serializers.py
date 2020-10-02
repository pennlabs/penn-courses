from rest_framework import serializers
from textwrap import dedent
from courses.serializers import SectionDetailSerializer
from plan.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    sections = SectionDetailSerializer(
        many=True, read_only=False, help_text="The sections in the schedule.", required=True
    )
    id = serializers.IntegerField(
        read_only=False, required=False,
        help_text="The id of the schedule."
    )

    class Meta:
        model = Schedule
        exclude = ["person"]
        extra_kwargs = {"semester": {"required": False}}
