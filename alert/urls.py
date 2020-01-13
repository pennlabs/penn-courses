from django.urls import include, path

import courses.views
from alert import views


urlpatterns = [
    path("", views.index, name="index"),
    path("courses/", courses.views.SectionList.as_view()),
    path("submitted", views.register, name="register"),
    path("resubscribe/<int:id_>", views.resubscribe, name="resubscribe"),
    path("webhook", views.accept_webhook, name="webhook"),
    path("api/submit", views.third_party_register, name="api-register"),
    path("s/", include("shortener.urls")),
]
