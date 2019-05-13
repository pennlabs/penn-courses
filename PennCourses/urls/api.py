from .base import *

urlpatterns = [
    path('', include('courses.urls')),
] + urlpatterns
