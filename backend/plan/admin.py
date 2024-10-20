from django.contrib import admin

from plan.models import Schedule


class ScheduleAdmin(admin.ModelAdmin):
    search_fields = ("person__username",)
    autocomplete_fields = ("person", "sections")

    list_filter = [
        "semester",
    ]


admin.site.register(Schedule, ScheduleAdmin)
