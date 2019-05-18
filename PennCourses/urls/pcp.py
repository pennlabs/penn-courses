from .base import *

urlpatterns = [
    path('registrar/', include('courses.urls')),
] + urlpatterns
