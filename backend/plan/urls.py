from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import (
    ScheduleViewSet,
    PrimaryScheduleViewSet,
    recommend_courses_view
)


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")
router.register(r"primary-schedules", PrimaryScheduleViewSet, basename="primary-schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path("", include(router.urls)),
]
