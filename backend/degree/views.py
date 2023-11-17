from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.db import IntegrityError
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from rest_framework.response import Response
from courses.models import Course

from degree.models import DegreePlan, Rule, UserDegreePlan

from degree.serializers import DegreePlanListSerializer, DegreePlanDetailSerializer, RuleSerializer, UserDegreePlanSerializer


class DegreeList(generics.ListAPIView):
    """
    Retrieve a list of (all) degrees available from a given year.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("degree-list"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}
            }
        },
    )

    serializer_class = DegreePlanListSerializer

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
            reverse_func("degree-detail", args=["graduation", "full_code"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Degree detail retrieved successfully."}
            }
        },
    )

    serializer_class = DegreePlanDetailSerializer
    queryset = DegreePlan.objects.all()



class UserDegreePlanViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    list, retrieve, create, update, and delete user degree plans.
    """

    schema = PcxAutoSchema(
        response_codes={
            "user-degree-plan-list": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]User degree plans listed successfully.",
                },
                "POST": {
                    201: "User degree plan successfully created.",
                    200: "User degree plan successfully updated (a user degree plan with the "
                    "specified id already existed).",
                    400: "Bad request (see description above).",
                },
            },
            "user-degree-plan-detail": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Successful retrieve "
                    "(the specified user degree plan exists).",
                    404: "No user degree plan with the specified id exists.",
                },
                "PUT": {
                    200: "Successful update (the specified schedule was found and updated).",
                    400: "Bad request (see description above).",
                    404: "No user degree plan with the specified id exists.",
                },
                "DELETE": {
                    204: "Successful delete (the specified user degree plan was found and deleted).",
                    404: "No schedule with the specified id exists.",
                },
            },
        },
    )

    serializer_class = UserDegreePlanSerializer
    http_method_names = ["get", "post", "delete", "put"]
    permission_classes = [IsAuthenticated]


    @staticmethod
    def get_courses(data):
        courses = data.get("courses", [])
        return [Course.objects.get(full_code=course["full_code"], semester=course["semester"]) for course in courses]


    def update(self, request, pk=None):
        if not UserDegreePlan.objects.filter(id=pk).exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            user_degree_plan = self.get_queryset().get(id=pk)
        except UserDegreePlan.DoesNotExist:
            return Response(
                {"detail": "You do not have access to the specified schedule."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            courses = self.get_courses(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more courses not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            user_degree_plan.person = request.user
            user_degree_plan.name = request.data.get("name")
            user_degree_plan.save()
            user_degree_plan.courses.set(courses)
            return Response({"message": "success", "id": user_degree_plan.id}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            return Response(
                {
                    "detail": "IntegrityError encountered while trying to update: "
                    + str(e.__cause__)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def create(self, request, *args, **kwargs):
        if UserDegreePlan.objects.filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))
        # NOTE: we do not use the provided id if it does not match an existing schedule

        try:
            courses = self.get_courses(request.data)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "One or more sections not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            degree_plan = DegreePlan.objects.get(request.data.get("degree_plan_id"))
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Degree plan not found in database."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_degree_plan = self.get_queryset().create(
                person=request.user,
                degree_plan=degree_plan,
                name=request.data.get("name"),
            )
            user_degree_plan.sections.set(courses)
            return Response(
                {"message": "success", "id": user_degree_plan.id},
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            return Response(
                {
                    "detail": "IntegrityError encountered while trying to create: "
                    + str(e.__cause__)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def get_queryset(self):
        queryset = UserDegreePlan.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            "courses",
            "degreeplan__rule_set",
        )
        return queryset
