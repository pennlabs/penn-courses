from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    path('plan/', include('plan.urls')),
    path('alert/', include('alert.urls')),
    path('courses/', include('courses.urls'))
] + [
    path('admin/', admin.site.urls),
    path('documentation/', include_docs_urls(title='API Docs')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
