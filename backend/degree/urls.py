from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from degree.views import (
    DegreePlanViewset,
    DegreeViewset,
    DockedCourseViewset,
    FulfillmentViewSet,
)


router = DefaultRouter(trailing_slash=False)
router.register(r"degreeplans", DegreePlanViewset, basename="degreeplan")
router.register(r"degrees", DegreeViewset, basename="degree")
router.register(r"docked", DockedCourseViewset)
fulfillments_router = NestedDefaultRouter(
    router, r"degreeplans", lookup="degreeplan", trailing_slash=False
)
fulfillments_router.register(
    r"fulfillments", FulfillmentViewSet, basename="degreeplan-fulfillment"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(fulfillments_router.urls)),
]
