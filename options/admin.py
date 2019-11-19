from django.contrib import admin

from .models import Option


class OptionAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']


admin.site.register(Option, OptionAdmin)
