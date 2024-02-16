from textwrap import dedent

from django.contrib.auth import get_user_model
from rest_framework import serializers

from courses.models import (
    Attribute,
    Course,
    Friendship,
    Instructor,
    Meeting,
    NGSSRestriction,
    PreNGSSRequirement,
    Section,
    StatusUpdate,
    UserProfile,
)
from plan.management.commands.recommendcourses import cosine_similarity


class MeetingSerializer(serializers.ModelSerializer):
    room = serializers.StringRelatedField(
        help_text=dedent(
            """
        The room in which the meeting is taking place, in the form '{building code} {room number}'.
        """
        )
    )

    class Meta:
        model = Meeting
        fields = ("day", "start", "end", "room")


class SectionIdSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="full_code")

    class Meta:
        model = Section
        fields = [
            "id",
            "activity",
        ]


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = ["id", "name"]


class MiniSectionSerializer(serializers.ModelSerializer):
    section_id = serializers.CharField(
        source="full_code",
        read_only=True,
        help_text=dedent(
            """
            The dash-separated dept, full-code, and section-code, e.g. `CIS-120-001` for the
            001 lecture section of CIS-120.
            """
        ),
    )
    instructors = InstructorSerializer(
        many=True,
        read_only=True,
        help_text="A list of the names of the instructors teaching this section.",
    )
    course_code = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent(
            """
            The full code of the course this section belongs to, e.g. `CIS-120` for CIS-120-001.
            """
        ),
    )
    course_title = serializers.SerializerMethodField(
        read_only=True,
        help_text=dedent(
            """
            The title of the course this section belongs to, e.g.
            'Programming Languages and Techniques I' for CIS-120-001.
            """
        ),
    )

    @staticmethod
    def get_course_code(obj):
        return obj.course.full_code

    @staticmethod
    def get_course_title(obj):
        return obj.course.title

    class Meta:
        model = Section
        fields = [
            "section_id",
            "status",
            "activity",
            "meeting_times",
            "instructors",
            "course_code",
            "course_title",
            "semester",
            "registration_volume",
        ]
        read_only_fields = fields


course_quality_help = "The average course quality rating for this section, on a scale of 0-4."
difficulty_help = "The average difficult rating for this section, on a scale of 0-4."
instructor_quality_help = "The average instructor quality for this section, on a scale of 0-4."
work_required_help = "The average work required for this section, on a scale of 0-4."


class SectionDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source="full_code",
        help_text=dedent(
            """
            The dash-separated dept, full-code, and section-code, e.g. `CIS-120-001` for the
            001 lecture section of CIS-120.
            """
        ),
    )
    meetings = MeetingSerializer(
        many=True,
        read_only=True,
        help_text=dedent(
            """
            A list of the meetings of this section (each meeting is a continuous span of time
            during which a section would meet).
            """
        ),
    )
    instructors = InstructorSerializer(
        read_only=True,
        many=True,
        help_text="A list of the names of the instructors teaching this section.",
    )
    associated_sections = SectionIdSerializer(
        many=True,
        read_only=True,
        help_text=dedent(
            """
        A list of all sections associated with the Course which this section belongs to; e.g. for
        CIS-120-001, all of the lecture and recitation sections for CIS-120 (including CIS-120-001)
        in the same semester.
        """
        ),
    )

    course_quality = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=course_quality_help
    )
    difficulty = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=difficulty_help
    )
    instructor_quality = serializers.DecimalField(
        max_digits=4,
        decimal_places=3,
        read_only=True,
        help_text=instructor_quality_help,
    )
    work_required = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=work_required_help
    )

    class Meta:
        model = Section
        fields = [
            "id",
            "status",
            "activity",
            "credits",
            "capacity",
            "semester",
            "meetings",
            "instructors",
            "course_quality",
            "instructor_quality",
            "difficulty",
            "work_required",
            "associated_sections",
            "registration_volume",
        ]
        read_only_fields = fields


class PreNGSSRequirementListSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(
        read_only=True,
        help_text="A string representation of the requirement, in the form '{code}@{school}'",
    )

    @staticmethod
    def get_id(obj):
        return f"{obj.code}@{obj.school}"

    class Meta:
        model = PreNGSSRequirement
        fields = ["id", "code", "school", "semester", "name"]
        read_only_fields = fields


class AttributeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ["code", "school", "description"]
        read_only_fields = fields


class NGSSRestrictionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NGSSRestriction
        fields = ["code", "restriction_type", "inclusive", "description"]
        read_only_fields = fields


class CourseListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source="full_code",
        help_text=dedent(
            """
        The full code of the course, in the form '{dept code}-{course code}'
        dash-joined department and code of the course, e.g. `CIS-120` for CIS-120."""
        ),
    )

    num_sections = type(
        "SerializerIntMethodField",
        (serializers.SerializerMethodField, serializers.IntegerField),
        dict(),
    )(read_only=True, help_text="The number of sections for this course.")

    recommendation_score = type(
        "SerializerDecimalMethodField",
        (serializers.SerializerMethodField, serializers.DecimalField),
        dict(),
    )(
        read_only=True,
        help_text=dedent(
            """
            The recommendation score for this course if the user is logged in, or null if the
            the user is not logged in."""
        ),
        max_digits=4,
        decimal_places=3,
    )

    def get_num_sections(self, obj):
        return obj.sections.count()

    def get_recommendation_score(self, obj):
        user_vector = self.context.get("user_vector")
        curr_course_vectors_dict = self.context.get("curr_course_vectors_dict")

        if user_vector is None or curr_course_vectors_dict is None:
            # NOTE: there should be no case in which user_vector is None
            # but curr_course_vectors_dict is not None. However, for
            # stability in production, recommendation_score is None when
            # either is None
            return None

        course_vector = curr_course_vectors_dict.get(obj.full_code)
        if course_vector is None:
            # Fires when the curr_course_vectors_dict is defined (ie, the user is authenticated)
            # but the course code is not in the model
            return None

        return cosine_similarity(course_vector, user_vector)

    course_quality = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=course_quality_help
    )
    difficulty = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=difficulty_help
    )
    instructor_quality = serializers.DecimalField(
        max_digits=4,
        decimal_places=3,
        read_only=True,
        help_text=instructor_quality_help,
    )
    work_required = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=work_required_help
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "semester",
            "num_sections",
            "course_quality",
            "instructor_quality",
            "difficulty",
            "work_required",
            "recommendation_score",
            "credits",
        ]
        read_only_fields = fields


class CourseDetailSerializer(CourseListSerializer):
    crosslistings = serializers.SlugRelatedField(
        slug_field="full_code",
        many=True,
        read_only=True,
        help_text=dedent(
            """
        A list of the full codes (DEPT-###) of all crosslistings for this course
        (not including this course).
        """
        ),
    )
    sections = SectionDetailSerializer(
        many=True, read_only=True, help_text="A list of the sections of this course."
    )
    pre_ngss_requirements = PreNGSSRequirementListSerializer(
        many=True,
        read_only=True,
        help_text=dedent(
            """
        A list of the pre-NGSS (deprecated since 2022B) academic requirements
        this course fulfills.
        """
        ),
    )

    attributes = AttributeListSerializer(
        many=True,
        read_only=True,
        help_text=dedent(
            """
        A list of attributes this course has. Attributes are typically
        used to mark courses which students in a program/major should
        take.
        """
        ),
    )

    restrictions = NGSSRestrictionListSerializer(
        many=True,
        read_only=True,
        help_text=dedent(
            """
        A list of NGSSRestrictions this course has. Restrictions provide information about
        who can take a course.
        """
        ),
    )

    course_quality = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=course_quality_help
    )
    difficulty = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=difficulty_help
    )
    instructor_quality = serializers.DecimalField(
        max_digits=4,
        decimal_places=3,
        read_only=True,
        help_text=instructor_quality_help,
    )
    work_required = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text=work_required_help
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "syllabus_url",
            "semester",
            "prerequisites",
            "course_quality",
            "instructor_quality",
            "difficulty",
            "work_required",
            "credits",
        ] + [
            "crosslistings",
            "pre_ngss_requirements",
            "attributes",
            "restrictions",
            "sections",
        ]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["email", "phone", "push_notifications"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(
        read_only=False,
        help_text="The user profile object, storing collected info about the user.",
        required=False,
    )

    def update(self, instance, validated_data):
        prof, _ = UserProfile.objects.get_or_create(user=instance)
        prof_data = validated_data.get("profile", None)
        for key in ["first_name", "last_name"]:
            if key in validated_data:
                setattr(instance, key, validated_data[key])
        if prof_data is not None:
            for key in ["phone", "email", "push_notifications"]:
                if key in prof_data:
                    setattr(prof, key, prof_data[key])
        prof.save()
        setattr(instance, "profile", prof)
        instance.save()
        return instance

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "profile"]
        read_only_fields = ["username"]


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name"]
        read_only_fields = ["username"]


class StatusUpdateSerializer(serializers.ModelSerializer):
    section = serializers.ReadOnlyField(
        source="section__full_code",
        read_only=True,
        help_text=dedent(
            """
            The code of the section which this status update applies to, in the form
            '{dept code}-{course code}-{section code}', e.g. `CIS-120-001` for the
            001 section of CIS-120.
            """
        ),
    )

    class Meta:
        model = StatusUpdate
        fields = ["section", "old_status", "new_status", "created_at", "alert_sent"]
        read_only_fields = fields


class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = ["sender", "recipient", "status", "sent_at", "accepted_at"]

    sender = PublicUserSerializer(
        read_only=True,
        help_text="The user that is sending the request.",
        required=False,
    )
    recipient = PublicUserSerializer(
        read_only=True,
        help_text="The user that is recieving the request.",
        required=False,
    )


class FriendshipRequestSerializer(serializers.Serializer):
    friend_id = serializers.IntegerField()

    def to_representation(self, instance):
        return super().to_representation(instance)
