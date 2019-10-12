from django.urls import path
from django.views.generic import TemplateView

from PennCourses.urls.base import urlpatterns


urlpatterns = [
    path('', TemplateView.as_view(template_name='plan_construction/index.html')),
] + urlpatterns
