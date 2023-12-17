from django.urls import include, path
from rest_framework import routers

from degree.views import (
    DegreeDetail,
    DegreeList,
    DegreePlanViewset,
    FulfillmentViewSet,
    rule_courses,
)


router = routers.DefaultRouter()

router.register("degreeplans", DegreePlanViewset, basename="degreeplans")
router.register("fulfillments", FulfillmentViewSet, basename="fulfillments")

urlpatterns = [
    path("degrees/", DegreeList.as_view(), name="degree-list"),
    path(
        "degree_detail/<degree_id>",
        DegreeDetail.as_view(),
        name="degree-detail",
    ),
    path("courses/<rule_id>", rule_courses, name="rule-courses"),
    path("", include(router.urls)),
]
