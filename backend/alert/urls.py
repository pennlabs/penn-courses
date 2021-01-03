from django.urls import include, path
from django.views.decorators.cache import cache_page
from rest_framework import routers

import courses.views
from alert import views
from alert.views import RegistrationHistoryViewSet, RegistrationViewSet
from courses.views import UserView


router = routers.DefaultRouter()
router.register(r"registrations", RegistrationViewSet, basename="registrations")
router.register(r"registrationhistory", RegistrationHistoryViewSet, basename="registrationhistory")

urlpatterns = [
    path("courses/", views.SectionStatsList.as_view(), name="section-search"),
    path(
        "<slug:semester>/sections/<slug:full_code>/statistics/",
        views.SectionStatsDetail.as_view(),  # cache_page(60 * 60)(views...)
        name="section-statistics-detail",
    ),
    path("webhook", views.accept_webhook, name="webhook"),
    path("settings/", UserView.as_view(), name="user-profile"),
    path("", include(router.urls)),
]
