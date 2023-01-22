from django.urls import path

from degree import views
from degree.views import DegreeListSearch

urlpatterns = [
    path("degrees/", views.DegreeList.as_view(), name="degree-list"),
    path(
        "search/degrees/",
        DegreeListSearch.as_view(),
        name="degree-search",
    ),
    path(
        "<slug:graduation>/degrees/<slug:full_code>/",
        views.DegreeDetail.as_view(),
        name="degree-detail",
    ),
]