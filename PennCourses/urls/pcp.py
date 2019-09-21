from django.urls import include, path

from PennCourses.urls.base import urlpatterns


urlpatterns = [
    path('', include('plan.urls')),
] + urlpatterns
