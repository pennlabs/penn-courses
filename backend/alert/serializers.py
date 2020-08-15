from rest_framework import serializers

from alert.models import Registration
from courses.models import Section


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(slug_field="full_code", required=False,
                                           queryset=Section.objects.none())
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)
    section_status = serializers.SerializerMethodField(read_only=True)

    is_active = serializers.SerializerMethodField()

    def get_section_status(self, o):
        return o.section.status

    def get_is_active(self, o):
        return o.is_active

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
            "deleted_at",
            "is_active",
            "section_status",
        ]
        read_only_fields = fields


class RegistrationCreateSerializer(serializers.Serializer):
    section = serializers.CharField(max_length=16)
    auto_resubscribe = serializers.BooleanField()

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
            "deleted_at",
            "is_active",
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
            "deleted_at",
            "section_status",
        ]


class RegistrationUpdateSerializer(serializers.Serializer):
    resubscribe = serializers.BooleanField()
    deleted = serializers.BooleanField()
    cancelled = serializers.BooleanField()
    auto_resubscribe = serializers.BooleanField()

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
            "deleted_at",
            "is_active",
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
            "deleted_at",
            "section_status",
        ]
