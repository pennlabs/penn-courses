from .base import *

urlpatterns = [
    path('courses/', include('courses.urls')),
] + urlpatterns
