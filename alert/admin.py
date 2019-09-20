from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import *


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('section_link', 'resubscribed_from', 'created_at')
    search_fields = ('email', 'phone', 'section__course__department', 'section__course__code', 'section__code')
    autocomplete_fields = ('section', )

    def section_link(self, instance):
        link = reverse('admin:pca_section_change', args=[instance.section.id])
        return format_html('<a href="{}">{}</a>', link, instance.section.__str__())


class CourseUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ('section', )
    readonly_fields = ('created_at', )


admin.site.register(Registration, RegistrationAdmin)
admin.site.register(CourseUpdate, CourseUpdateAdmin)
