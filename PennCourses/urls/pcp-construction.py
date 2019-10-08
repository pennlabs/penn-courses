from django.urls import include, path
from django.views.generic import TemplateView

from PennCourses.urls.base import urlpatterns


urlpatterns = [
    path('', TemplateView.as_view(template_name='plan/index.html')),
] + urlpatterns
