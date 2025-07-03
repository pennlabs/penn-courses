from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework_nested import routers

from plan.views import (
    BreakViewSet,
    CalendarAPIView,
    PrimaryScheduleViewSet,
    ScheduleViewSet,
    recommend_courses_view,
)


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")
router.register(r"primary-schedules", PrimaryScheduleViewSet, basename="primary-schedules")

urlpatterns = [
    path("<int:schedule_pk>/calendar/", CalendarAPIView.as_view(), name="calendar-view"),
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path(
        "breaks/<int:break_pk>/",
        BreakViewSet.as_view({"delete": "destroy"}),
        name="break-detail",
    ),
    path("breaks/", BreakViewSet.as_view({"post": "create", "put": "update"}), name="break-list"),
    path("", include(router.urls)),
]
