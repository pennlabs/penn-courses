from django_auto_prefetching import AutoPrefetchViewSetMixin
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404
from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.models import Course
from courses.serializers import CourseListSerializer
from degree.models import Degree, DegreePlan, Fulfillment, Rule, DockedCourse
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    FulfillmentSerializer,
    DockedCourseSerializer
)


class DegreeViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Degree objects.
    """

    # queryset = Degree.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["program", "degree", "concentration", "year"]
    filterset_fields = search_fields

    def get_queryset(self):
            queryset = Degree.objects.all()
            degree_id = self.request.query_params.get('id', None)
            if degree_id is not None:
                queryset = queryset.filter(id=degree_id)
            return queryset
    
    def get_serializer_class(self):
        if self.action == "list":
            if self.request.query_params.get('id', None) is not None:
                return DegreeDetailSerializer
            return DegreeListSerializer
        return DegreeDetailSerializer

class DegreePlanViewset(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a DegreePlan.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DegreePlan.objects.filter(person=self.request.user)
        queryset = queryset.prefetch_related(
            "fulfillments",
            "degrees",
            "degrees__rules",
        )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return DegreePlanListSerializer
        else:
            return DegreePlanDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context
    
    def retrieve(self, request, *args, **kwargs):
        degree_plan = self.get_object()
        serializer = self.get_serializer(degree_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        if request.data.get("name") is None:
            raise ValidationError({ "name": "This field is required." })
        new_degree_plan = DegreePlan(name=request.data.get("name"), person=self.request.user)
        new_degree_plan.save()
        serializer = self.get_serializer(new_degree_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
    @action(detail=True, methods=["post"])
    def copy(self, request, pk=None):
        """
        Copy a degree plan.
        """
        if request.data.get("name") is None:
            raise ValidationError({ "name": "This field is required." })
        degree_plan = self.get_object()
        new_degree_plan = degree_plan.copy(request.data["name"])
        serializer = self.get_serializer(new_degree_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post", "delete"])
    def degrees(self, request, pk=None):
        degree_id = request.data.get("degree_id")
        if degree_id is None:
            raise ValidationError({ "degree_ids": "This field is required." })
        degree_plan = self.get_object()

        try:
            print("c")
            if request.method == "POST":
                degree_plan.degrees.add(degree_id)
            elif request.method == "DELETE":
                degree_plan.degrees.remove(degree_id)
                print("here")
                return Response(status=status.HTTP_204_NO_CONTENT)
        except IntegrityError:
            print("error")
            return Response(
                data={"error": "One or more of the degrees does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(degree_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FulfillmentViewSet(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a Fulfillment.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = FulfillmentSerializer
    http_method_names = ["get", "post", "head", "delete"]
    queryset = Fulfillment.objects.all()
    lookup_field = "full_code"

    def get_degree_plan_id(self):
        degreeplan_pk = self.kwargs["degreeplan_pk"]
        try:
            return int(degreeplan_pk)
        except (ValueError, TypeError):
            raise ValidationError("Invalid degreeplan_pk passed in URL")

    def get_queryset(self):
        queryset = Fulfillment.objects.filter(
            degree_plan__person=self.request.user,
            degree_plan_id=self.get_degree_plan_id(),
        )
        return queryset
    
    def create(self, request, *args, **kwargs):
        if request.data.get("full_code") is None:
            raise ValidationError({ "full_code": "This field is required." })
        self.kwargs["full_code"] = request.data["full_code"]
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)

@api_view(["GET"])
def courses_for_rule(request, rule_id: int):
    """
    Search for courses that fulfill a given rule.
    """


class DockedCourseViewset(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update docked courses
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DockedCourseSerializer
    # http_method_names = ["get", "post", "head", "delete"]
    queryset = DockedCourse.objects.all()
    lookup_field = "full_code"

    def get_queryset(self):
        queryset = DockedCourse.objects.filter(person=self.request.user)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})  # used to get the user
        return context
    
    # def retrieve(self, request, *args, **kwargs):
    #     dockedCourse = self.get_object()
    #     serializer = self.get_serializer(dockedCourse)
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        if request.data.get("full_code") is None:
            raise ValidationError({ "full_code": "This field is required." })
        self.kwargs["full_code"] = request.data["full_code"]
        self.kwargs["person"] = self.request.user
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)
        
    def destroy(self, request, *args, **kwargs):
        if kwargs["full_code"] is None:
            raise ValidationError({ "full_code": "This field is required." })

        instances_to_delete = self.get_queryset().filter(full_code=kwargs["full_code"])
        
        if not instances_to_delete.exists():
            raise Http404("No instances matching the provided full_code were found.")

        for instance in instances_to_delete:
            self.perform_destroy(instance)
        
        return Response(status.HTTP_200_OK)
