from django.urls import path, include
from rest_framework import routers
from degree.views import DegreeDetail, DegreeList, UserDegreePlanViewset

router = routers.DefaultRouter()

router.register("degreeplans", UserDegreePlanViewset, basename="degreeplans")

urlpatterns = [
    path("degrees/<int:year>", DegreeList.as_view(), name="degree-list"),
    path(
        "degree_detail/<pk>",
        DegreeDetail.as_view(),
        name="degree-detail",
    ),
    path("", include(router.urls)),
]
