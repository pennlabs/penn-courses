from django.urls import path

from courses import views
from courses.views import CourseListSearch


urlpatterns = [
    path("<slug:semester>/courses/", views.CourseList.as_view(), name="courses-list"),
    path("<slug:semester>/search/courses/", CourseListSearch.as_view(), name="courses-search"),
    path(
        "<slug:semester>/courses/<slug:full_code>/",
        views.CourseDetail.as_view(),
        name="courses-detail",
    ),
    path("<slug:semester>/search/sections/", views.SectionList.as_view(), name="section-search"),
    path(
        "<slug:semester>/sections/<slug:full_code>/",
        views.SectionDetail.as_view(),
        name="sections-detail",
    ),
    path(
        "<slug:semester>/requirements/",
        views.PreNGSSRequirementList.as_view(),
        name="requirements-list",
    ),
    path("statusupdate/<slug:full_code>/", views.StatusUpdateView.as_view(), name="statusupdate"),
]
