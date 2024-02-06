from django.contrib import admin
from django.conf.urls import url
from django.template.response import TemplateResponse

from degree.models import Degree, DegreePlan, DoubleCountRestriction, Rule, SatisfactionStatus

# Register your models here.
admin.site.register(Rule)
admin.site.register(DegreePlan)
admin.site.register(SatisfactionStatus)
admin.site.register(DoubleCountRestriction)

@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    def get_urls(self):

        # get the default urls
        urls = super().get_urls()
        custom_urls = [
            url(r'^degree-editor/$', self.admin_site.admin_view(self.security_configuration))
        ]
        # Make sure here you place your added urls first than the admin default urls
        return custom_urls + urls

    # Your view definition fn
    def security_configuration(self, request):
        context = dict(
            self.admin_site.each_context(request), # Include common variables for rendering the admin template.
        )
        return TemplateResponse(request, "degree-editor.html", context)