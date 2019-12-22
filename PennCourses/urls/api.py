from django.urls import include, path

from PennCourses.urls.base import urlpatterns


urlpatterns = [
    path('^plan', include('plan.urls')),
    path('^alert', include('alert.urls')),
] + urlpatterns
