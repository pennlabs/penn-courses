from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import re_path, reverse
from django.utils.html import format_html

from degree.models import (
    Degree,
    DegreePlan,
    DoubleCountRestriction,
    Fulfillment,
    PDPBetaUser,
    Rule,
    SatisfactionStatus,
)


# Register your models here.
class RuleAdmin(admin.ModelAdmin):
    search_fields = ["title", "id"]
    list_display = ["title", "id", "parent"]
    list_select_related = ["parent"]


class PDPBetaUserAdmin(admin.ModelAdmin):
    search_fields = ("person__username", "person__id")
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
admin.site.register(DegreePlan)
admin.site.register(SatisfactionStatus)
admin.site.register(PDPBetaUser, PDPBetaUserAdmin)
admin.site.register(Fulfillment, FulfillmentAdmin)
admin.site.register(DoubleCountRestriction, DoubleCountRestrictionAdmin)
admin.site.register(Degree, DegreeAdmin)
