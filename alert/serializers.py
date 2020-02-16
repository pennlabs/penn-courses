from rest_framework import serializers

from alert.models import Registration


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(slug_field='full_code', read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'created_at', 'original_created_at', 'updated_at', 'section', 'user', 'deleted',
                  'auto_resubscribe', 'notification_sent', 'notification_sent_at', 'deleted_at']
        read_only_fields = ['created_at', 'original_created_at', 'updated_at', 'section', 'user', 'notification_sent',
                            'notification_sent_at', 'deleted_at']
