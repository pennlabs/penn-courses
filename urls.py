from django.urls import path
from . import views

urlpatterns = [
    path('<slug:short>', views.index, name='index'),
]
