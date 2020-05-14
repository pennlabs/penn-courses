from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from alert.views import accept_webhook
from courses.views import UserView, open_api


urlpatterns = [
    path("plan/", include("plan.urls")),
    path("alert/", include("alert.urls")),
    path("courses/", include("courses.urls")),
    path("options/", include("options.urls", namespace="options")),
    path(
        "openapi/",
        open_api,
        name="openapi-schema",
    ),
    path(
        "documentation/",
        TemplateView.as_view(
            template_name="redoc.html", extra_context={"schema_url": "openapi-schema"}
        ),
        name="documentation",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/me/", UserView.as_view()),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("api/", include(urlpatterns)),
    path("webhook", accept_webhook, name="webhook"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
