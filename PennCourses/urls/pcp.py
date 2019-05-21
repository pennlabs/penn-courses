from .base import *

urlpatterns = [
    path('', include('plan.urls')),
] + urlpatterns
