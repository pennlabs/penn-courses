from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from courses.models import (APIKey, APIPrivilege, Building, Course, Department, Instructor,
                            Meeting, Requirement, Restriction, Room, Section, StatusUpdate)


class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ('code', )


class InstructorAdmin(admin.ModelAdmin):
    search_fields = ('name', )


class CourseAdmin(admin.ModelAdmin):
    search_fields = ('full_code', 'department__code', 'code', 'semester')
    autocomplete_fields = ('department', 'primary_listing')
    readonly_fields = ('crosslistings', )
    list_filter = ('semester', )

    list_select_related = (
        'department',
    )

    def crosslistings(self, instance):
        return format_html_join('\n', '<li><a href="{}">{}</li>',
                                ((reverse('admin:courses_course_change', args=[c.id]), str(c), )
                                 for c in instance.crosslistings.all()))


class SectionAdmin(admin.ModelAdmin):
    search_fields = ('full_code', 'course__department__code', 'course__code', 'code', 'course__semester')
    readonly_fields = ('course_link',)
    autocomplete_fields = ('instructors', 'course', 'associated_sections', )
    list_filter = ('course__semester', )
    list_display = ['full_code', 'semester', 'status']

    list_select_related = (
        'course',
        'course__department'
    )

    def course_link(self, instance):
        link = reverse('admin:courses_course_change', args=[instance.course.id])
        return format_html('<a href="{}">{}</a>', link, instance.course.__str__())


class MeetingAdmin(admin.ModelAdmin):
    list_select_related = (
        'section',
        'room',
        'room__building',
        'section__course',
        'section__course__department',
    )


class RequirementAdmin(admin.ModelAdmin):
    autocomplete_fields = ('departments', 'courses', 'overrides')


class StatusUpdateAdmin(admin.ModelAdmin):
    autocomplete_fields = ('section', )
    readonly_fields = ('created_at', )
    list_select_related = [
        'section',
        'section__course',
        'section__course__department'
    ]


admin.site.register(APIKey)
admin.site.register(APIPrivilege)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Building)
admin.site.register(Room)
admin.site.register(Requirement, RequirementAdmin)
admin.site.register(Restriction)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(StatusUpdate, StatusUpdateAdmin)
