from django.contrib import admin

from plan.models import Schedule


class ScheduleAdmin(admin.ModelAdmin):
    search_fields = ("person",)
    autocomplete_fields = ("person", "sections")


admin.site.register(Schedule, ScheduleAdmin)
