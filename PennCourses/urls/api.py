from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

from courses.views import UserView


urlpatterns = [
    path('plan/', include('plan.urls')),
    path('alert/', include('alert.urls')),
    path('courses/', include('courses.urls')),
    path(
        'openapi/',
        get_schema_view(title='Penn Courses Documentation', public=True),
        name='openapi-schema',
    ),
    path(
        'documentation/',
        TemplateView.as_view(
            template_name='redoc.html', extra_context={'schema_url': 'openapi-schema'}
        ),
        name='documentation',
    ),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/me/', UserView.as_view()),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('api/', include(urlpatterns))
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
