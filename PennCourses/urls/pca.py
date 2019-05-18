from django.urls import path, include

from .base import *
from alert.views import index

urlpatterns = [
    path('', index),
    path('s/', include('shortener.urls')),
] + urlpatterns
