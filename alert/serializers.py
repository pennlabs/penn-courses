from rest_framework import serializers

from alert.models import Registration


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(slug_field='full_code')
    user = serializers.SlugRelatedField(slug_field='username')

    class Meta:
        model = Registration
        fields = ['created_at', 'updated_at', 'section', 'user', 'deleted', 'muted', 'auto_mute']
