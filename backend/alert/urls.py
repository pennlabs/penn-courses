from django.urls import include, path
from rest_framework import routers

import courses.views
from alert import views
from alert.views import RegistrationHistoryViewSet, RegistrationViewSet
from courses.views import UserView


router = routers.DefaultRouter()
router.register(r"registrations", RegistrationViewSet, basename="registrations")
router.register(r"registrationhistory", RegistrationHistoryViewSet, basename="registrationhistory")

urlpatterns = [
    path("courses/", courses.views.SectionList.as_view(), name="section-search"),
    path("webhook", views.accept_webhook, name="webhook"),
    path("api/settings/", UserView.as_view(), name="user-profile"),
    path("api/", include(router.urls)),
]
