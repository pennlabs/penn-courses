from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import ScheduleViewSet


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("", include(router.urls)),
]
