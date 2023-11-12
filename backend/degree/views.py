from rest_framework import generics

from degree.models import DegreePlan
from degree.serializers import DegreePlanDetailSerializer, DegreePlanSerializer
from PennCourses.docs_settings import PcxAutoSchema


class DegreeList(generics.ListAPIView):
    """
    Retrieve a list of (all) degrees available from a given year.
    """

    schema = PcxAutoSchema(
        response_codes={
            "degree-list": {"GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}}
        },
    )

    serializer_class = DegreePlanSerializer

    def get_queryset(self):
        year = self.kwargs["year"]
        queryset = DegreePlan.objects.filter(year=year)
        return queryset


class DegreeDetail(generics.RetrieveAPIView):
    """
    Retrieve a detailed look at a specific degree. Includes all details necessary to display degree
    info, including degree requirements that this degree needs.
    """

    schema = PcxAutoSchema(
        response_codes={
            "degree-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Degree detail retrieved successfully."}
            }
        },
    )

    serializer_class = DegreePlanDetailSerializer
    queryset = DegreePlan.objects.all()
