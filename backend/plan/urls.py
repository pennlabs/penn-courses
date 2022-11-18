from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import ScheduleViewSet, recommend_courses_view, advanced_registration_schedule_view


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path("advanced-registration/", advanced_registration_schedule_view, name="advanced-registration-schedule"),
    path("", include(router.urls)),
]
