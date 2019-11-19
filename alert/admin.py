from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from alert.models import Registration


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('section_link', 'resubscribed_from', 'created_at')
    search_fields = ('email',
                     'phone',
                     'section__full_code',
                     'section__course__departm',
                     'section__course__code',
                     'section__code')
    autocomplete_fields = ('section', )

    list_filter = ['section__course__semester']

    list_select_related = (
        'section',
        'section__course',
        'section__course__department',
    )

    def section_link(self, instance):
        link = reverse('admin:courses_section_change', args=[instance.section.id])
        return format_html('<a href="{}">{}</a>', link, instance.section.__str__())


admin.site.register(Registration, RegistrationAdmin)
