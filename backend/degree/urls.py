from django.urls import path, include
from rest_framework import routers
from degree.views import DegreeDetail, DegreeList, UserDegreePlanViewset, rule_courses

router = routers.DefaultRouter()

router.register("degreeplans", UserDegreePlanViewset, basename="degreeplans")

urlpatterns = [
    path("degrees/", DegreeList.as_view(), name="degree-list"),
    path(
        "degree_detail/<pk>",
        DegreeDetail.as_view(),
        name="degree-detail",
    ),
    path("courses/<rule_id>", rule_courses, name="rule-courses"),
    path("", include(router.urls)),
]
