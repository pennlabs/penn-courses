from django.urls import include, path
from rest_framework import routers

from alert import views
from alert.views import RegistrationHistoryViewSet, RegistrationViewSet


router = routers.DefaultRouter()
router.register(r"registrations", RegistrationViewSet, basename="registrations")
router.register(r"registrationhistory", RegistrationHistoryViewSet, basename="registrationhistory")

urlpatterns = [
    path("webhook", views.accept_webhook, name="webhook"),
    path("", include(router.urls)),
]
