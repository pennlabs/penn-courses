from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('courses', views.get_sections, name='courses'),
    path('submitted', views.register, name='register'),
    path('resubscribe/<int:id_>', views.resubscribe, name='resubscribe'),
    path('webhook', views.accept_webhook, name='webhook'),
]
