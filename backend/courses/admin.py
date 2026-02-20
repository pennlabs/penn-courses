from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from courses.management.commands.recompute_topics import recompute_topics
from courses.models import (
    APIKey,
    APIPrivilege,
    Attribute,
    Building,
    Course,
    Department,
    Instructor,
    Meeting,
    NGSSRestriction,
    PreNGSSRequirement,
    PreNGSSRestriction,
    Room,
    Section,
    StatusUpdate,
    Topic,
    UserProfile,
)


# User Profile: https://github.com/sibtc/django-admin-user-profile
class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ("code",)


class InstructorAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    autocomplete_fields = ("user",)


class AttributeAdmin(admin.ModelAdmin):
    search_fields = (
        "code",
        "description",
    )
    list_display = ("code", "school", "description")
    exclude = ("courses",)


class NGSSRestrictionAdmin(admin.ModelAdmin):
    search_fields = (
        "code",
        "restriction_type",
        "description",
    )
    list_display = ("code", "restriction_type", "inclusive", "description")
    exclude = ("courses",)


class CourseAdmin(admin.ModelAdmin):
    search_fields = ("full_code", "department__code", "code", "semester", "title")
    autocomplete_fields = ("department", "primary_listing", "parent_course")
    readonly_fields = ("topic", "crosslistings", "course_attributes")
    exclude = ("attributes",)
    list_filter = ("semester",)
    list_display = ("full_code", "semester", "title")

    list_select_related = ("department",)

    def save_model(self, request, obj, form, change):
        """
        Overridden to set `manually_set_parent_course` to True if `parent_course` is modified.
        """
        must_recompute_topics = False
        if "parent_course" in form.changed_data:
            obj.manually_set_parent_course = True
            must_recompute_topics = True

        super().save_model(request, obj, form, change)

        if must_recompute_topics:
            recompute_topics(min_semester=obj.semester, verbose=True)

    def crosslistings(self, instance):
        return format_html_join(
            "\n",
            '<li><a href="{}">{}</li>',
            (
                (
                    reverse("admin:courses_course_change", args=[c.id]),
                    str(c),
                )
                for c in instance.crosslistings.all()
            ),
        )

    def course_attributes(self, instance):
        return format_html_join(
            "\n",
            '<li><a href="{}">{}</li>',
            (
                (
                    reverse("admin:courses_attribute_change", args=[a.id]),
                    str(a),
                )
                for a in instance.attributes.all()
            ),
        )


class TopicAdmin(admin.ModelAdmin):
    readonly_fields = (
        "courses",
        "branched_from",
    )
    search_fields = (
        "id",
        "most_recent__full_code",
    )
    list_select_related = ("most_recent",)

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("most_recent").prefetch_related("courses")
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Hack to limit most_recent choices to courses of the same Topic
        if db_field.name == "most_recent" and request.resolver_match.kwargs.get("object_id"):
            topic_id = request.resolver_match.kwargs["object_id"]
            kwargs["queryset"] = Course.objects.filter(topic_id=topic_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def courses(self, instance):
        t = loader.get_template("topic_courses_admin.html")
        courses = instance.courses.all()
        for course in courses:
            course.a_link = reverse("admin:courses_course_change", args=[course.id])
        return t.render({"courses": instance.courses.all()})

    def branched_from_id(self, instance):
        """
        The original topic from which this topic branched.
        """
        if instance.branched_from_id is None:
            return "None"
        link = reverse("admin:courses_topic_change", args=[instance.branched_from_id])
        return format_html('<a href="{}">{}</a>', link, str(instance.branched_from_id))


class SectionAdmin(admin.ModelAdmin):
    search_fields = (
        "full_code",
        "course__department__code",
        "course__code",
        "code",
        "course__semester",
    )
    readonly_fields = ("course_link",)
    autocomplete_fields = (
        "instructors",
        "course",
        "associated_sections",
    )
    list_filter = ("course__semester",)

    list_display = ["full_code", "semester", "status"]

    list_select_related = ("course", "course__department")

    def get_object(self, request, object_id, from_field=None):
        # Hook obj for use in formfield_for_manytomany
        self.obj = super().get_object(request, object_id, from_field)
        return self.obj

    def course_link(self, instance):
        link = reverse("admin:courses_course_change", args=[instance.course.id])
        return format_html('<a href="{}">{}</a>', link, instance.course.__str__())


class MeetingAdmin(admin.ModelAdmin):
    list_select_related = (
        "section",
        "room",
        "room__building",
        "section__course",
        "section__course__department",
    )
    autocomplete_fields = ["section"]


class PreNGSSRequirementAdmin(admin.ModelAdmin):
    autocomplete_fields = ("departments", "courses", "overrides")


class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ("section",)
    readonly_fields = ("created_at",)
    list_filter = ("section__course__semester",)
    list_select_related = ["section", "section__course", "section__course__department"]
    search_fields = ("section__full_code",)


admin.site.register(APIKey)
admin.site.register(APIPrivilege)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Building)
admin.site.register(Room)
admin.site.register(PreNGSSRequirement, PreNGSSRequirementAdmin)
admin.site.register(PreNGSSRestriction)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(StatusUpdate, StatusUpdateAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(NGSSRestriction, NGSSRestrictionAdmin)

# https://github.com/sibtc/django-admin-user-profile
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
