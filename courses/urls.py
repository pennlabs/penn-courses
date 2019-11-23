from django.urls import path

from . import views


urlpatterns = [
    path('<slug:semester>/courses/', views.CourseList.as_view()),
    path('<slug:semester>/courses/<slug:full_code>/',  views.CourseDetail.as_view()),
    path('<slug:semester>/requirements/', views.RequirementList.as_view()),
    path('statusupdate/<slug:full_code>/', views.StatusUpdateView.as_view()),
]
