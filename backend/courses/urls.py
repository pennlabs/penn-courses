from django.urls import path

from courses import views
from courses.views import CourseListSearch
from courses.views import send_friendship_request, remove_friendship, handle_friendship_request, cancel_friendship_request


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
    path("frienship/send_request", send_friendship_request, name="send-friendship-request"),
    path("frienship/remove_friend", remove_friendship, name="remove-friendship"),
    path("frienship/handle_request", handle_friendship_request, name="handle-friendship-request"),
    path("frienship/cancel_request", cancel_friendship_request, name="cancel-friendship-request"),
]
