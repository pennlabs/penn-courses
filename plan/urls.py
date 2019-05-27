from django.urls import path

from .views import CourseListSearch, CourseDetailSearch
from courses.views import RequirementList

urlpatterns = [
    # omit semester parameter, since PCP only cares about the current semester.
    path('courses/', CourseListSearch.as_view()),
    path('courses/<slug:full_code>/', CourseDetailSearch.as_view()),
    path('requirements/', RequirementList.as_view()),
]
