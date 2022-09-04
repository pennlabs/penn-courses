from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import ScheduleViewSet, recommend_courses_view, penn_mobile_schedule_view


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path("penn-mobile-schedule/", penn_mobile_schedule_view, name="penn-mobile-schedule"),
    path("", include(router.urls)),
]
