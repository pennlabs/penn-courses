from textwrap import dedent

from django.core.cache import cache
from django.db.models import Count, Max, Min
from rest_framework import serializers

from alert.models import Registration
from courses.models import Section, StatusUpdate, string_dict_to_html
from courses.util import get_current_semester


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
    "close_notification",
    "close_notification_sent",
    "close_notification_sent_at",
    "deleted_at",
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
    is_active = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent(
            """
        True if the registration would send an alert hen the watched section changes to open,
        False otherwise. This is equivalent to not(notification_sent or deleted or cancelled).
        """
        ),
    )
    is_waiting_for_close = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent(
            """
        True if the registration is waiting to send a close notification to the user
        once the section closes.  False otherwise.
        """
        ),
    )

    def get_section_status(self, registration_object):
        return registration_object.section.status

    def get_is_active(self, registration_object):
        return registration_object.is_active

    def get_is_waiting_for_close(self, registration_object):
        return registration_object.is_waiting_for_close

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
            f for f in registration_fields if f not in ["section", "auto_resubscribe", "id"]
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
        read_only_fields = [f for f in registration_fields if f != "auto_resubscribe"]


def normalize(value, min, max):
    """
    This function normalizes the given value to a 0-1 scale based on the given min and max.
    Raises ValueError if min >= max.
    """
    if min >= max:
        raise ValueError(f"normalize called with min >= max ({min} >= {max})")
    return float(value - min) / float(max - min)


class SectionStatisticsSerializer(serializers.ModelSerializer):
    section_id = serializers.CharField(
        source="full_code",
        help_text=dedent(
            """
            The dash-separated dept, full-code, and section-code, e.g. 'CIS-120-001' for the
            001 lecture section of CIS-120.
            """
        ),
    )
    instructors = serializers.StringRelatedField(
        many=True, help_text="A list of the names of the instructors teaching this section.",
    )
    course_title = serializers.SerializerMethodField(
        help_text=dedent(
            """
            The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.
            """
        ),
    )
    current_popularity = serializers.SerializerMethodField(
        help_text=dedent(
            """
            The current popularity of the section, which is defined as:
            [the number of active PCA registrations for this section]/[the class capacity]
            mapped onto the range [0,1] where the lowest current popularity (across all sections)
            maps to 0 and the highest current popularity maps to 1.
            NOTE: sections with an invalid class capacity (0 or negative) are excluded from
            computation of the statistic, and if this section has an invalid class capacity, then
            this method will return None (or null in JSON).
            """
        ),
    )

    def get_course_title(self, obj):
        return obj.course.title

    def get_current_popularity(self):
        """
        The current popularity of the section, which is defined as:
        [the number of active PCA registrations for this section]/[the class capacity]
        mapped onto the range [0,1] where the lowest current popularity (across all sections)
        maps to 0 and the highest current popularity maps to 1.
        NOTE: sections with an invalid class capacity (0 or negative) are excluded from
        computation of the statistic, and if this section has an invalid class capacity, then
        this method will return None (or null in JSON).
        """
        from alert.models import Registration  # imported here to avoid circular imports

        if self.capacity == 0:
            return None

        section_popularity_extrema = cache.get("section_popularity_extrema")
        if section_popularity_extrema is None:
            section_popularity_extrema = (
                Registration.objects.filter(
                    section__course__semester=get_current_semester(), section__capacity__gt=0
                )
                .values("section", "section__capacity")
                .annotate(score=Count("section") / Max("section__capacity"))
                .aggregate(min=Min("score"), max=Max("score"))
            )
            cache.set("section_popularity_extrema", section_popularity_extrema, timeout=(60 * 60))

        if section_popularity_extrema.min == section_popularity_extrema.max:
            return 0.5
        this_score = float(Registration.objects.filter(section=self).count()) / float(self.capacity)
        # normalize(...) maps the range [aggregate_scores.min, aggregate_scores.max] to [0,1] and
        # returns the position of this_score on this new range
        return normalize(this_score, section_popularity_extrema.min, section_popularity_extrema.max)

    class Meta:
        model = Section
        fields = [
            "section_id",
            "status",
            "activity",
            "meeting_times",
            "instructors",
            "course_title",
            "current_popularity",
        ]
        read_only_fields = fields

    @staticmethod
    def get_semester(obj):
        return obj.course.semester
