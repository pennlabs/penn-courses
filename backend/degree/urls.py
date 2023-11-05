from django.urls import path
from degree import views
from degree.views import DegreeListSearch

urlpatterns = [
    path(
        "degrees/",
        views.DegreeList.as_view(),
        name="degree-list"),
    path(
        "search/degrees/",
        DegreeListSearch.as_view(),
        name="degree-search",
    ),
    path(
        "degrees/<slug:graduation>/<slug:full_code>/",
        views.DegreeDetail.as_view(),
        name="degree-detail",
    ),
    path(
        "rules/",
        views.RuleList.as_view(),
        name="rule-list"
    )
]
