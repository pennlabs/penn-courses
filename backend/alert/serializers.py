from textwrap import dedent

from rest_framework import serializers

from alert.models import Registration
from courses.models import Section, StatusUpdate, string_dict_to_html


registration_fields = [
    "id",
    "created_at",
    "original_created_at",
    "updated_at",
    "section",
    "user",
    "cancelled",
    "cancelled_at",
    "deleted",
    "deleted_at",
    "auto_resubscribe",
    "notification_sent",
    "notification_sent_at",
    "last_notification_sent_at",
    "close_notification",
    "close_notification_sent",
    "close_notification_sent_at",
    "is_active",
    "is_waiting_for_close",
]


class RegistrationSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(
        slug_field="full_code",
        required=False,
        queryset=Section.objects.none(),
        help_text="The dash-separated full code of the section associated with this Registration.",
    )
    user = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True,
        help_text="The Penn Labs Accounts username of the User who owns this Registration.",
    )
    section_status = serializers.SerializerMethodField(
        read_only=True,
        help_text="The current status of the watched section. Options and meanings: "
        + string_dict_to_html(dict(StatusUpdate.STATUS_CHOICES)),
    )

    def get_section_status(self, registration_object):
        return registration_object.section.status

    class Meta:
        model = Registration
        fields = registration_fields + ["is_active", "section_status"]
        read_only_fields = fields


class RegistrationCreateSerializer(serializers.ModelSerializer):
    section = serializers.CharField(
        max_length=16,
        help_text="The dash-separated full code of the section associated with this Registration.",
    )
    auto_resubscribe = serializers.BooleanField(
        required=False,
        help_text=dedent(
            """
        Set this to true to turn on auto resubscribe (causing the registration to automatically
        resubscribe once it sends out a notification).  Default is false if not specified.
        """
        ),
    )
    id = serializers.IntegerField(
        read_only=False,
        required=False,
        help_text="The id of the registration (can optionally be used to customize the "
        "id of a new registration, or to update an existing registration).",
    )

    class Meta:
        model = Registration
        fields = registration_fields
        read_only_fields = [
            f
            for f in registration_fields
            if f not in ["section", "auto_resubscribe", "close_notification", "id"]
        ]


class RegistrationUpdateSerializer(serializers.ModelSerializer):
    resubscribe = serializers.BooleanField(
        required=False,
        help_text=dedent(
            """
        Set this to true to resubscribe to this registration (only works if the registration
        has sent a notification and hasn't been deleted).
        """
        ),
    )
    deleted = serializers.BooleanField(
        required=False,
        help_text=dedent(
            """
        Set this to true to delete this registration (making it inactive and preventing it from
        showing up in List Registrations).
        """
        ),
    )
    cancelled = serializers.BooleanField(
        required=False,
        help_text=dedent(
            """
        Set this to true to cancel to this registration (making it inactive while keeping it
        in List Registration).
        """
        ),
    )
    auto_resubscribe = serializers.BooleanField(
        required=False,
        help_text=dedent(
            """
        Set this to true to turn on auto resubscribe (causing the registration to automatically
        resubscribe once it sends out a notification).
        """
        ),
    )

    class Meta:
        model = Registration
        fields = registration_fields + ["cancelled", "deleted", "resubscribe"]
        read_only_fields = [
            f for f in registration_fields if f not in ["auto_resubscribe", "close_notification"]
        ]
