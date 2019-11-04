from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

from courses.views import CourseDetail, RequirementList

from .views import CourseListSearch, ScheduleViewSet


router = routers.DefaultRouter()
router.register(r'schedules', ScheduleViewSet, basename='schedules')


urlpatterns = [
    # omit semester parameter, since PCP only cares about the current semester.
    path('courses/', CourseListSearch.as_view()),
    path('courses/<slug:full_code>/', CourseDetail.as_view()),
    path('requirements/', RequirementList.as_view()),
    path('', TemplateView.as_view(template_name='plan/build/index.html')),
    path('', include(router.urls)),
]
