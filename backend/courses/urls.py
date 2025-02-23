from django.urls import path

from courses import views
from courses.views import CourseListSearch, Health


urlpatterns = [
    path("health/", Health.as_view(), name="health"),
    path("<slug:semester>/courses/", views.CourseList.as_view(), name="courses-list"),
    path(
        "<slug:semester>/search/courses/",
        CourseListSearch.as_view(),
        name="courses-search",
    ),
    path(
        "<slug:semester>/courses/<slug:full_code>/",
        views.CourseDetail.as_view(),
        name="courses-detail",
    ),
    path(
        "<slug:semester>/search/sections/",
        views.SectionList.as_view(),
        name="section-search",
    ),
    path(
        "<slug:semester>/sections/<slug:full_code>/",
        views.SectionDetail.as_view(),
        name="sections-detail",
    ),
    path(
        "<slug:semester>/pre-ngss-requirements/",
        views.PreNGSSRequirementList.as_view(),
        name="requirements-list",
    ),
    path(
        "attributes/",
        views.AttributeList.as_view(),
        name="attributes-list",
    ),
    path(
        "restrictions/",
        views.NGSSRestrictionList.as_view(),
        name="restrictions-list",
    ),
    path("statusupdate/<slug:full_code>/", views.StatusUpdateView.as_view(), name="statusupdate"),
    path("friendship/", views.FriendshipView.as_view(), name="friendship"),
]
