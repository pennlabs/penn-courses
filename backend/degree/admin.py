from django.contrib import admin

from degree.models import Degree, Rule, DegreePlan, SatisfactionStatus, DoubleCountRestriction


# Register your models here.
admin.site.register(Degree)
admin.site.register(Rule)
admin.site.register(DegreePlan)
admin.site.register(SatisfactionStatus)
admin.site.register(DoubleCountRestriction)
