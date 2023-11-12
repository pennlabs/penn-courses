from django.urls import path
from degree.views import DegreeList, DegreeDetail

urlpatterns = [
    path("degrees/<int:year>", DegreeList.as_view(), name="degree-list"),
    path(
        "degree_detail/<pk>",
        DegreeDetail.as_view(),
        name="degree-detail",
    ),
]
