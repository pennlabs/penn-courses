from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import ScheduleViewSet, recommend_courses_view, recommend_schedule_view


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/schedule/", recommend_schedule_view, name="recommend-schedule"),
    path("recommendations/courses/", recommend_courses_view, name="recommend-courses"),
    path("", include(router.urls)),
]
