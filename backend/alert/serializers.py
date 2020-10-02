from rest_framework import serializers
from textwrap import dedent

from alert.models import Registration
from courses.models import Section, StatusUpdate, string_dict_to_html


registration_fields = [
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
]


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(
        slug_field="full_code", required=False, queryset=Section.objects.none(),
        help_text="The dash-separated full code of the section associated with this Registration."
    )
    user = serializers.SlugRelatedField(
        slug_field="username", read_only=True,
        help_text="The Penn Labs Accounts username of the User who owns this Registration."
    )
    section_status = serializers.SerializerMethodField(
        read_only=True,
        help_text="The current status of the watched section. Options and meanings: "
        + string_dict_to_html(dict(StatusUpdate.STATUS_CHOICES))
    )
    is_active = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent("""
        True if the registration would send an alert hen the watched section changes to open,
        False otherwise. This is equivalent to not(notification_sent or deleted or cancelled).
        """)
    )

    def get_section_status(self, o):
        return o.section.status

    def get_is_active(self, o):
        return o.is_active

    class Meta:
        model = Registration
        fields = registration_fields + [
            "is_active",
            "section_status"
        ]
        read_only_fields = fields


class RegistrationCreateSerializer(serializers.ModelSerializer):
    section = serializers.CharField(max_length=16)
    auto_resubscribe = serializers.BooleanField(required=False)

    class Meta:
        model = Registration
        fields = registration_fields
        read_only_fields = [f for f in registration_fields if f not in [
            "section",
            "auto_resubscribe"
        ]]


class RegistrationUpdateSerializer(serializers.ModelSerializer):
    resubscribe = serializers.BooleanField(required=False)
    deleted = serializers.BooleanField(required=False)
    cancelled = serializers.BooleanField(required=False)
    auto_resubscribe = serializers.BooleanField(required=False)

    class Meta:
        model = Registration
        fields = registration_fields + [
            "cancelled",
            "deleted",
            "resubscribe"
        ]
        read_only_fields = [f for f in registration_fields if f != "auto_resubscribe"]
