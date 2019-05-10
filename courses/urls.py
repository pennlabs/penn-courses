from django.urls import path

from . import views
urlpatterns = [
    path('sections/', views.SectionList.as_view()),
    path('courses/', views.CourseList.as_view()),
    path('courses/<int:pk>/', views.CourseDetail.as_view())
]