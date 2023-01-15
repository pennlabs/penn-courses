from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework_nested import routers

from plan.views import ScheduleViewSet, recommend_courses_view, CalendarAPIView


router = routers.DefaultRouter()
router.register(r"schedules", ScheduleViewSet, basename="schedules")

schedules_router = routers.NestedSimpleRouter(router, r"schedules", lookup="schedules")

schedules_router.register(
    r"calendar/<slug:user_secretuuid>/",
    CalendarAPIView.as_view(),
    basename="calendar-view",
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="plan/build/index.html")),
    path("recommendations/", recommend_courses_view, name="recommend-courses"),
    path("", include(router.urls)),
]
