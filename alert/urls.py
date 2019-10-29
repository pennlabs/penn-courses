from django.urls import path

import courses.views
from alert import views


urlpatterns = [
    path('', views.index, name='index'),
    # path('courses', views.get_sections, name='courses'),
    path('courses/', courses.views.SectionList.as_view()),
    path('submitted', views.register, name='register'),
    path('resubscribe/<int:id_>', views.resubscribe, name='resubscribe'),
    path('webhook', views.accept_webhook, name='webhook'),
    path('api/submit', views.third_party_register, name='api-register')
]
