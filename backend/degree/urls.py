from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from degree.views import (
    DegreeDetail,
    DegreeList,
    DegreePlanViewset,
    FulfillmentViewSet,
    courses_for_rule,
)


router = DefaultRouter()
router.register(r"degreeplans", DegreePlanViewset, basename="degreeplan")
fulfillments_router = NestedDefaultRouter(router, r"degreeplans", lookup="degreeplan")
fulfillments_router.register(r"fulfillments", FulfillmentViewSet, basename="degreeplan-fulfillment")

urlpatterns = [
    path("degrees/", DegreeList.as_view(), name="degree-list"),
    path(
        "degree_detail/<degree_id>",
        DegreeDetail.as_view(),
        name="degree-detail",
    ),
    path("courses/<rule_id>", courses_for_rule, name="courses-for-rule"),
    path("", include(router.urls)),
    path("", include(fulfillments_router.urls)),
]
