from rest_framework import serializers

from courses.serializers import SectionDetailSerializer
from plan.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    sections = SectionDetailSerializer(many=True, read_only=False)

    class Meta:
        model = Schedule
        exclude = ['person']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            'sections',
        )
        return queryset
