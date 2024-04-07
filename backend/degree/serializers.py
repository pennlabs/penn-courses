from textwrap import dedent

from django.db.models import Q
from rest_framework import serializers

from courses.models import Course
from courses.serializers import CourseListSerializer, CourseDetailSerializer
from degree.models import (
    Degree,
    DegreePlan,
    DoubleCountRestriction,
    Fulfillment,
    Rule,
    DockedCourse,
    CourseTaken,
    DegreeProfile,
    UserProfile,
)
from courses.util import get_current_semester
from degree.models import (
    Degree,
    DegreePlan,
    DockedCourse,
    DoubleCountRestriction,
    Fulfillment,
    Rule,
    CourseTaken,
    DegreeProfile
)




class DegreeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = "__all__"


class SimpleCourseSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source="full_code",
        help_text=dedent(
            """
        The full code of the course, in the form '{dept code}-{course code}'
        dash-joined department and code of the course, e.g. `CIS-120` for CIS-120."""
        ),
    )

    course_quality = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text="course_quality_help"
    )
    difficulty = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text="difficulty_help"
    )
    instructor_quality = serializers.DecimalField(
        max_digits=4,
        decimal_places=3,
        read_only=True,
        help_text="instructor_quality_help",
    )
    work_required = serializers.DecimalField(
        max_digits=4, decimal_places=3, read_only=True, help_text="work_required_help"
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "credits",
            "semester",
            "course_quality",
            "instructor_quality",
            "difficulty",
            "work_required",
        ]
        read_only_fields = fields


class RuleSerializer(serializers.ModelSerializer):
    q_json = serializers.ReadOnlyField(help_text="JSON representation of the q object")

    class Meta:
        model = Rule
        fields = "__all__"


# Allow recursive serialization of rules
RuleSerializer._declared_fields["rules"] = RuleSerializer(
    many=True, read_only=True, source="children"
)


class DoubleCountRestrictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoubleCountRestriction
        fields = "__all__"


class DegreeDetailSerializer(serializers.ModelSerializer):
    rules = RuleSerializer(many=True, read_only=True)
    double_count_restrictions = DoubleCountRestrictionSerializer(many=True, read_only=True)

    class Meta:
        model = Degree
        fields = "__all__"


class FulfillmentSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()

    def get_course(self, obj):
        course = (
            Course.with_reviews.filter(
                full_code=obj.full_code, semester__lte=get_current_semester()
            )
            .order_by("-semester")
            .first()
        )
        if course is not None:
            return SimpleCourseSerializer(course).data
        return None

    rules = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Rule.objects.all(), required=False
    )

    def to_internal_value(self, data):
        """
        Allow for this route to be nested under the degreeplan viewset.
        """
        data = data.copy()
        data["degree_plan"] = self.context["view"].get_degree_plan_id()
        return super().to_internal_value(data)

    class Meta:
        model = Fulfillment
        fields = ["id", "degree_plan", "full_code", "course", "semester", "rules"]

    def validate(self, data):
        data = super().validate(data)
        rules = data.get("rules")  # for patch requests without a rules field
        full_code = data.get("full_code")
        degree_plan = data.get("degree_plan")

        if rules is None and full_code is None and degree_plan is None:
            return data  # Nothing to validate
        if rules is None and self.instance is not None:
            rules = self.instance.rules.all()
        elif rules is None:
            rules = []
        if full_code is None:
            full_code = self.instance.full_code
        if degree_plan is None:
            degree_plan = self.instance.degree_plan

        # TODO: check that rules belong to this degree plan
        for rule in rules:
            # NOTE: we don't do any validation if the course doesn't exist in DB. In future,
            # it may be better to prompt user for manual override
            if (
                Course.objects.filter(full_code=full_code).exists()
                and not Course.objects.filter(rule.get_q_object(), full_code=full_code).exists()
            ):
                raise serializers.ValidationError(
                    f"Course {full_code} does not satisfy rule {rule.id}"
                )

        # Check for double count restrictions
        double_count_restrictions = DoubleCountRestriction.objects.filter(
            Q(rule__in=rules) | Q(other_rule__in=rules)
        )
        for restriction in double_count_restrictions:
            if restriction.is_double_count_violated(degree_plan):
                raise serializers.ValidationError(
                    f"Double count restriction {restriction.id} violated"
                )

        return data


class DegreePlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DegreePlan
        fields = ["id", "name", "created_at", "updated_at"]


class DegreePlanDetailSerializer(serializers.ModelSerializer):
    degrees = DegreeDetailSerializer(
        many=True, help_text="The degrees belonging to this degree plan"
    )

    person = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DegreePlan
        fields = ["id", "name", "degrees", "person", "created_at", "updated_at"]


class DockedCourseSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(help_text="The id of the docked course")

    class Meta:
        model = DockedCourse
        fields = ["full_code", "id"]



class CourseTakenSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())

    class Meta:
        model = CourseTaken
        fields = ["course", "semester", "grade"]


class DegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Degree
        fields = "__all__"

    def validate_degrees(self, degrees):
        if not all(Degree.objects.filter(id=degree_id).exists() for degree_id in degrees):
            raise serializers.ValidationError("Degree(s) not valid")
        return degrees


class DegreeProfileSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(help_text="The id of the degree profile")
    courses_taken = CourseTakenSerializer(source="coursetaken_set", many=True, required=False)
    degrees = DegreeSerializer(many=True, required=False)

    class Meta:
        model = DegreeProfile
        fields = ["id", "user_profile", "graduation_date", "degrees", "courses_taken"]

    def create(self, data):
        degrees_data = data.pop("degrees", [])
        courses_taken_data = data.pop("courses_taken", [])

        user_profile_id = data.pop("user_profile")
        user_profile = UserProfile.objects.get(id=user_profile_id)

        degree_profile = DegreeProfile.objects.create(user_profile=user_profile, **data)

        if degrees_data:
            degrees = Degree.objects.filter(id__in=degrees_data)
            degree_profile.degrees.set(degrees)

        for course_taken_data in courses_taken_data:
            CourseTaken.objects.create(degree_profile=degree_profile, **course_taken_data)

        return degree_profile


class DegreeProfilePatchSerializer(serializers.ModelSerializer):
    degrees = serializers.PrimaryKeyRelatedField(queryset=Degree.objects.all(), many=True)

    class Meta:
        model = DegreeProfile
        fields = ["degrees", "graduation_date"]
