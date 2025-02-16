from textwrap import dedent
from rest_framework import serializers

from courses.serializers import PublicUserSerializer, SectionDetailSerializer, MeetingSerializer, MeetingWithBuildingSerializer
from plan.models import PrimarySchedule, Schedule, Break


class ScheduleSerializer(serializers.ModelSerializer):
    sections = SectionDetailSerializer(
        many=True, read_only=False, help_text="The sections in the schedule.", required=True
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


class BreakSerializer(serializers.ModelSerializer):

    meetings = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent(
            """
            A list of the meetings of this section (each meeting is a continuous span of time
            during which a section would meet).
            """
        ),
    )
    id = serializers.IntegerField(
        read_only=False, required=False, help_text="The id of the schedule."
    )


    class Meta:
        model = Break
        exclude = ["person"]
        

    def get_meetings(self, obj):
        include_location = self.context.get("include_location", False)
        if include_location:
            meetings_serializer = MeetingWithBuildingSerializer(obj.meetings, many=True)
        else:
            meetings_serializer = MeetingSerializer(obj.meetings, many=True)

        return meetings_serializer.data

