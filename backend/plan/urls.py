from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from plan.views import (
    ScheduleViewSet,
    get_shared_schedule,
    recommend_courses_view,
    set_shared_schedule,
)


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")


urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path("shared/get_schedule", get_shared_schedule, name="get-shared-schedule"),
    path("shared/set_schedule", set_shared_schedule, name="set-shared-schedule"),
    path("", include(router.urls)),
]
