from django.contrib import admin

from degree.models import DegreePlan, Rule


# Register your models here.
admin.site.register(DegreePlan)
admin.site.register(Rule)
