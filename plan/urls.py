from django.urls import path

from . import views
from courses.views import CourseDetail

urlpatterns = [
    # omit semester parameter, since PCP only cares about the current semester.
    path('courses/', views.CourseListSearch.as_view()),
    path('courses/<slug:full_code>/', CourseDetail.as_view()),
]
