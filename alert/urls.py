from django.urls import include, path
from rest_framework import routers

import courses.views
from alert import views
from alert.views import RegistrationViewSet
from courses.views import UserDataViewSet


router = routers.DefaultRouter()
router.register(r'registrations', RegistrationViewSet, basename='registrations')
router.register(r'settings', UserDataViewSet, basename='settings')

urlpatterns = [
    path('', views.index, name='index'),
    path('courses/', courses.views.SectionList.as_view()),
    path('submitted', views.register, name='register'),
    path('resubscribe/<int:id_>', views.resubscribe, name='resubscribe'),
    path('webhook', views.accept_webhook, name='webhook'),
    path('api/submit', views.third_party_register, name='api-register'),
    path('api', include(router.urls)),
]
