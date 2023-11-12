from rest_framework import serializers

from courses.serializers import PublicUserSerializer, SectionDetailSerializer
from plan.models import PrimarySchedule, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    sections = SectionDetailSerializer(
        many=True,
        read_only=False,
        help_text="The sections in the schedule.",
        required=True,
    )
    id = serializers.IntegerField(
        read_only=False, required=False, help_text="The id of the schedule."
    )

    class Meta:
        model = Schedule
        exclude = ["person"]
        extra_kwargs = {"semester": {"required": False}}


class PrimaryScheduleSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(
        read_only=True,
        help_text="The primary schedule.",
        required=False,
    )

    user = PublicUserSerializer(
        read_only=True,
        help_text="The user to which the primary schedule belongs.",
        required=False,
    )

    class Meta:
        model = PrimarySchedule
        fields = ["user", "schedule"]
