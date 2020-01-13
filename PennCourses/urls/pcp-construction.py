from django.urls import path
from django.views.generic.base import RedirectView

from PennCourses.urls.base import urlpatterns


urlpatterns = [path("", RedirectView.as_view(url="https://penncourseplan.com")),] + urlpatterns
