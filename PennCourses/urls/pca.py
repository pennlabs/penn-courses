from django.urls import path, include

from .base import *
import alert.urls

urlpatterns = alert.urls.urlpatterns + urlpatterns
