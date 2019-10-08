from django.urls import path
from django.views.generic import TemplateView

from courses.views import RequirementList

from .views import CourseDetailSearch, CourseListSearch


urlpatterns = [
    # omit semester parameter, since PCP only cares about the current semester.
    path('courses/', CourseListSearch.as_view()),
    path('courses/<slug:full_code>/', CourseDetailSearch.as_view()),
    path('requirements/', RequirementList.as_view()),
    path('', TemplateView.as_view(template_name='plan/build/index.html')),
]
