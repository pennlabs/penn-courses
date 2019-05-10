from django.urls import path

from . import views
urlpatterns = [
    path('sections/', views.SectionList.as_view()),
]