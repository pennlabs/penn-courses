from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from alert.models import AddDropPeriod, PcaDemandDistributionEstimate, Registration


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = (
        "head_registration_id",
        "section_link",
        "resubscribed_from",
        "created_at",
    )
    search_fields = (
        "email",
        "phone",
        "section__full_code",
        "section__course__department__code",
    )
    autocomplete_fields = ("section",)

    exclude = ["head_registration"]

    ordering = ("-created_at",)

    list_filter = [
        "notification_sent",
        "section__course__semester",
        ("resubscribed_to", admin.EmptyFieldListFilter),
    ]

    list_select_related = (
        "section",
        "section__course",
        "section__course__department",
    )

    def section_link(self, instance):
        link = reverse("admin:courses_section_change", args=[instance.section.id])
        return format_html('<a href="{}">{}</a>', link, instance.section.__str__())

    def head_registration_id(self, instance):
        link = reverse(
            "admin:alert_registration_change", args=[instance.head_registration_id]
        )
        return format_html(
            '<a href="{}">{}</a>', link, str(instance.head_registration_id)
        )


class PcaDemandDistributionEstimateAdmin(admin.ModelAdmin):
    search_fields = ("created_at",)

    autocomplete_fields = ("highest_demand_section", "lowest_demand_section")

    list_filter = ["semester", "created_at"]

    def has_change_permission(self, request, obj=None):
        """
        Don't allow PcaDemandDistributionEstimate objects to be changed in the Admin console
        (although they can be deleted).
        """
        return False


class AddDropPeriodAdmin(admin.ModelAdmin):
    search_fields = ("semester",)

    list_filter = ["semester"]


admin.site.register(Registration, RegistrationAdmin)
admin.site.register(PcaDemandDistributionEstimate, PcaDemandDistributionEstimateAdmin)
admin.site.register(AddDropPeriod, AddDropPeriodAdmin)
