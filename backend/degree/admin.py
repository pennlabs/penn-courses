from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import re_path, reverse
from django.utils.html import format_html

from degree.models import (
    Degree,
    DegreePlan,
    DoubleCountRestriction,
    DualProgram,
    Fulfillment,
    PDPBetaUser,
    PDPOnboardingStatus,
    ProgramVariant,
    Rule,
    SatisfactionStatus,
)


# Register your models here.
class RuleAdmin(admin.ModelAdmin):
    search_fields = ["title", "id"]
    list_display = ["title", "id", "parent"]
    list_select_related = ["parent"]


class PDPBetaUserAdmin(admin.ModelAdmin):
    search_fields = ("person__username", "person__id", "person__email")
    autocomplete_fields = ("person",)
    list_display = ("person", "email", "status", "created_at", "decided_at")
    list_filter = ("status",)
    readonly_fields = ("created_at", "decided_at")
    actions = ["approve", "deny"]

    def get_queryset(self, request):
        return PDPBetaUser.pending_first(super().get_queryset(request).select_related("person"))

    @admin.display(ordering="person__email")
    def email(self, obj):
        return obj.person.email

    def decide(self, request, queryset, status):
        changed = list(queryset.exclude(status=status))
        for beta in changed:
            beta.decide(status)
        self.message_user(request, f"{len(changed)} user(s) {status.label.lower()}.")

    @admin.action(description="Approve selected users")
    def approve(self, request, queryset):
        self.decide(request, queryset, PDPBetaUser.Status.APPROVED)

    @admin.action(description="Deny selected users")
    def deny(self, request, queryset):
        self.decide(request, queryset, PDPBetaUser.Status.DENIED)

    def save_model(self, request, obj, form, change):
        # A new row is a decision too: adding someone approved should email them.
        if not change or "status" in form.changed_data:
            obj.decide(obj.status)
        else:
            super().save_model(request, obj, form, change)


class PDPOnboardingStatusAdmin(admin.ModelAdmin):
    search_fields = ("person__username", "person__id")
    list_display = ("person", "has_been_onboarded", "updated_at")
    autocomplete_fields = ("person",)


class FulfillmentAdmin(admin.ModelAdmin):
    autocomplete_fields = ["rules"]


class DoubleCountRestrictionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["rule", "other_rule"]


class DegreeAdmin(admin.ModelAdmin):
    autocomplete_fields = ["rules"]
    list_display = [
        "program",
        "degree",
        "major",
        "concentration",
        "year",
        "view_degree_editor",
    ]

    def view_degree_editor(self, obj):
        return format_html(
            '<a href="{url}?id={id}">View in Degree Editor</a>',
            id=obj.id,
            url=reverse("admin:degree-editor"),
        )

    def get_urls(self):
        # get the default urls
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r"^degree-editor/$",
                self.admin_site.admin_view(self.degree_editor),
                name="degree-editor",
            )
        ]
        return custom_urls + urls

    def degree_editor(self, request):
        context = dict(self.admin_site.each_context(request))
        return TemplateResponse(request, "degree-editor.html", context)


admin.site.register(Rule, RuleAdmin)
admin.site.register(ProgramVariant)
admin.site.register(DualProgram)
admin.site.register(DegreePlan)
admin.site.register(SatisfactionStatus)
admin.site.register(PDPBetaUser, PDPBetaUserAdmin)
admin.site.register(PDPOnboardingStatus, PDPOnboardingStatusAdmin)
admin.site.register(Fulfillment, FulfillmentAdmin)
admin.site.register(DoubleCountRestriction, DoubleCountRestrictionAdmin)
admin.site.register(Degree, DegreeAdmin)
