from rest_framework import serializers

from alert.models import Registration


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(slug_field="full_code", read_only=True)
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    section_status = serializers.SerializerMethodField()

    is_active = serializers.SerializerMethodField()
    is_waiting_for_close = serializers.SerializerMethodField()

    def get_section_status(self, o):
        return o.section.status

    def get_is_active(self, o):
        return o.is_active

    def get_is_waiting_for_close(self, o):
        return o.is_waiting_for_close

    class Meta:
        model = Registration
        fields = [
            "id",
            "created_at",
            "original_created_at",
            "updated_at",
            "section",
            "user",
            "deleted",
            "auto_resubscribe",
            "notification_sent",
            "notification_sent_at",
            "close_notification",
            "close_notification_sent",
            "close_notification_sent_at",
            "push_notifications",
            "deleted_at",
            "is_active",
            "is_waiting_for_close",
            "section_status",
        ]
        read_only_fields = [
            "created_at",
            "original_created_at",
            "updated_at",
            "section",
            "user",
            "notification_sent",
            "notification_sent_at",
            "close_notification_sent",
            "close_notification_sent_at",
            "deleted_at",
            "is_active",
            "is_waiting_for_close",
            "section_status",
        ]
