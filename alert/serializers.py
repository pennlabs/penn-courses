from django.db.models import Prefetch
from rest_framework import serializers

from alert.models import Registration
from courses.models import Section
from courses.serializers import MiniSectionSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    section = MiniSectionSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ['created_at', 'updated_at', 'section', 'deleted', 'muted', 'auto_mute']

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            Prefetch('section', Section.with_reviews.all()),
        )
        return queryset
