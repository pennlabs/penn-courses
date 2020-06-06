from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.views.generic import TemplateView
from PennCourses.docs_settings import openapi_description, JSONOpenAPICustomTagGroupsRenderer
from rest_framework.schemas import get_schema_view

from alert.views import accept_webhook
from courses.views import UserView

api_urlpatterns = [
    path("plan/", include("plan.urls")),
    path("alert/", include("alert.urls")),
    path("courses/", include("courses.urls")),
    path("options/", include("options.urls", namespace="options")),
    path(
        "openapi/",
        get_schema_view(title="Penn Courses API Documentation", public=True,
                        description=openapi_description,
                        renderer_classes=[JSONOpenAPICustomTagGroupsRenderer]),
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
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path("admin/", admin.site.urls),
    path("accounts/me/", UserView.as_view()),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("api/", include(api_urlpatterns)),
    path("webhook", accept_webhook, name="webhook"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
