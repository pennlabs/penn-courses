from rest_framework import serializers

from alert.models import Registration
from courses.serializers import MiniSectionSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    section = MiniSectionSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ['created_at', 'updated_at', 'section', 'deleted', 'muted', 'auto_mute']
