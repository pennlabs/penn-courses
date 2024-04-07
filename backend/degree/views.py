from django.db import IntegrityError
from django.http import Http404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from degree.models import Degree, DegreePlan, DockedCourse, Fulfillment, PDPBetaUser, DegreeProfile, UserProfile
from degree.serializers import (
    DegreeDetailSerializer,
    DegreeListSerializer,
    DegreePlanDetailSerializer,
    DegreePlanListSerializer,
    DockedCourseSerializer,
    FulfillmentSerializer,
    DockedCourseSerializer,
    DegreeProfileSerializer,
    CourseTakenSerializer,
    DegreeProfilePatchSerializer,
)


class InPDPBeta(BasePermission):
    def has_permission(self, request, view):
        return PDPBetaUser.objects.filter(person=request.user).exists()


class DegreeViewset(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve a list of all Degree objects.
    """

    filter_backends = [SearchFilter]
    search_fields = ["program", "degree", "concentration", "year"]
    filterset_fields = search_fields

    # After Beta: remove this permission entirely
    permission_classes = [IsAuthenticated & InPDPBeta]

    queryset = Degree.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return DegreeListSerializer
        return DegreeDetailSerializer


class DegreePlanViewset(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update a DegreePlan.
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]

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
            raise ValidationError({"name": "This field is required."})
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
            raise ValidationError({"name": "This field is required."})
        degree_plan = self.get_object()
        new_degree_plan = degree_plan.copy(request.data["name"])
        serializer = self.get_serializer(new_degree_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post", "delete"])
    def degrees(self, request, pk=None):
        """
        Add or remove degrees from a degree plan.
        """
        degree_ids = request.data.get("degree_ids")
        if not isinstance(degree_ids, list):
            raise ValidationError({"degree_ids": "This field must be a list."})
        if degree_ids is None:
            raise ValidationError({"degree_ids": "This field is required."})
        degree_plan = self.get_object()

        try:
            if request.method == "POST":
                degree_plan.degrees.add(*degree_ids)
            elif request.method == "DELETE":
                degree_plan.degrees.remove(*degree_ids)
                return Response(status=status.HTTP_204_NO_CONTENT)
        except IntegrityError:
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

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]
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
        """
        Create or update fulfillment.
        """
        if request.data.get("full_code") is None:
            raise ValidationError({"full_code": "This field is required."})
        self.kwargs["full_code"] = request.data["full_code"]
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)


class DockedCourseViewset(viewsets.ModelViewSet):
    """
    List, retrieve, create, destroy, and update docked courses
    """

    # After beta: remove InPDPBeta
    permission_classes = [IsAuthenticated & InPDPBeta]
    serializer_class = DockedCourseSerializer
    http_method_names = ["get", "post", "head", "delete"]
    queryset = DockedCourse.objects.all()
    lookup_field = "full_code"

    def get_queryset(self):
        queryset = DockedCourse.objects.filter(person=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        if request.data.get("full_code") is None:
            raise ValidationError({"full_code": "This field is required."})
        self.kwargs["full_code"] = request.data["full_code"]
        self.kwargs["person"] = self.request.user
        try:
            return self.partial_update(request, *args, **kwargs)
        except Http404:
            return super().create(request, *args, **kwargs)
    

class DegreeProfileViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DegreeProfileSerializer

    def get_queryset(self):
        return DegreeProfile.objects.filter(user_profile__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DegreeProfilePatchSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        user_profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return serializer.save(user_profile=user_profile.id)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user_profile.user != request.user:
            return Response(
                {"detail": "Unable to delete profile."}, status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="add-course", url_name="add_course")
    def add_course(self, request, pk=None):
        degree_profile = self.get_object()
        serializer = CourseTakenSerializer(data=request.data)
        if serializer.is_valid():
            degree_profile = self.get_object()
            degree_profile.add_course(
                course_id=serializer.validated_data["course"].id,
                semester=serializer.validated_data["semester"],
                grade=serializer.validated_data["grade"],
            )
            return Response({"status": "course added"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="remove-course", url_name="remove_course")
    def remove_course(self, request, pk=None):
        degree_profile = self.get_object()
        course_id = request.data.get("course")
        semester = request.data.get("semester")

        if not course_id or not semester:
            return Response(
                {"error": "missing course id or semester"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            degree_profile.remove_course(course_id=course_id, semester=semester)
            return Response({"status": "course removed"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
