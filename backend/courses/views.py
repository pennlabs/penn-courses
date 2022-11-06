from datetime import timezone

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from courses.models import User
from courses.filters import CourseSearchFilterBackend
from courses.models import (
    Attribute,
    Course,
    Friendship,
    NGSSRestriction,
    PreNGSSRequirement,
    Section,
    StatusUpdate,
)
from courses.search import TypedCourseSearchBackend, TypedSectionSearchBackend
from courses.serializers import (
    AttributeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    MiniSectionSerializer,
    NGSSRestrictionListSerializer,
    PreNGSSRequirementListSerializer,
    SectionDetailSerializer,
    StatusUpdateSerializer,
    UserSerializer,
)
from courses.util import get_current_semester
from PennCourses.docs_settings import PcxAutoSchema, reverse_func
from plan.management.commands.recommendcourses import retrieve_course_clusters, vectorize_user


SEMESTER_PARAM_DESCRIPTION = (
    "The semester of the course (of the form YYYYx where x is A [for spring], "
    "B [summer], or C [fall]), e.g. '2019C' for fall 2019. Alternatively, you "
    "can just pass 'current' for the current semester."
)


class BaseCourseMixin(AutoPrefetchViewSetMixin, generics.GenericAPIView):
    @staticmethod
    def get_semester_field():
        return "semester"

    def get_semester(self):
        semester = self.kwargs.get("semester", "current")
        if semester == "current":
            semester = get_current_semester(allow_not_found=True)
            semester = semester if semester is not None else "all"

        return semester

    def filter_by_semester(self, queryset):
        # if we're in a view without a semester parameter, only return the current semester.
        semester = self.get_semester()
        if semester != "all":
            queryset = queryset.filter(**{self.get_semester_field(): semester})
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_semester(queryset)
        return queryset


class SectionList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of sections (less detailed than [PCx] Section, or SectionDetail on the
    backend).  The sections are filtered by the search term (assumed to be a prefix of a
    section's full code, with each chunk either space-delimited, dash-delimited, or not delimited).
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("section-search", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Sections Listed Successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("section-search", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = MiniSectionSerializer
    queryset = Section.with_reviews.all().exclude(activity="")
    filter_backends = [TypedSectionSearchBackend]
    search_fields = ["^full_code"]

    @staticmethod
    def get_semester_field():
        return "course__semester"


class SectionDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course section.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("sections-detail", args=["semester", "full_code"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Section detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("sections-detail", args=["semester", "full_code"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = SectionDetailSerializer
    queryset = Section.with_reviews.all()
    lookup_field = "full_code"

    def get_semester_field(self):
        return "course__semester"


class CourseList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of (all) courses for the provided semester.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("courses-list", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-list", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = CourseListSerializer
    queryset = Course.with_reviews.filter(sections__isnull=False)  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.filter(sections__isnull=False)
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related("course", "meetings__room"),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class CourseListSearch(CourseList):
    """
    This route allows you to list courses by certain search terms and/or filters.
    Without any GET parameters, this route simply returns all courses
    for a given semester. There are a few filter query parameters which constitute ranges of
    floating-point numbers. The values for these are <min>-<max> , with minimum excluded.
    For example, looking for classes in the range of 0-2.5 in difficulty, you would add the
    parameter difficulty=0-2.5. If you are a backend developer, you can find these filters in
    backend/plan/filters.py/CourseSearchFilterBackend. If you are reading the frontend docs,
    these filters are listed below in the query parameters list (with description starting with
    "Filter").
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("courses-search", args=["semester"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully.",
                    400: "Bad request (invalid query).",
                }
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-search", args=["semester"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    def get_serializer_context(self):
        """
        This method overrides the default `get_serializer_context` (from super class)
        in order to add the `user_vector` and `curr_course_vectors_dict`
        key/value pairs to the serializer context dictionary. If there is no authenticated user
        (ie `self.request.user.is_authenticated` is `False`) or `self.request` is `None`,
        the value associated with the `user_vector` and `curr_course_vectors_dict`key are not set.
        All other key/value pairs that would have been returned by the default
        `get_serializer_context` (which is `CourseList.get_serializer_context`) are in the
        dictionary returned in this method. `user_vector` and `curr_course_vectors_dict` encode the
        vectors used to calculate the recommendation score for a course for a user (see
        `backend/plan/management/commands/recommendcourses.py` for details on the vectors).
        Note that for testing purposes, this implementation of get_serializer_context is replaced
        with simply `CourseList.get_serializer_context` to reduce the costly process of training the
        model in unrelated tests. You can see how this is done and how to override that behavior in
        in `backend/tests/__init__.py`.
        """
        context = super().get_serializer_context()

        if self.request is None or not self.request.user or not self.request.user.is_authenticated:
            return context

        _, _, curr_course_vectors_dict, past_course_vectors_dict = retrieve_course_clusters()
        user_vector, _ = vectorize_user(
            self.request.user, curr_course_vectors_dict, past_course_vectors_dict
        )
        context.update(
            {"user_vector": user_vector, "curr_course_vectors_dict": curr_course_vectors_dict}
        )

        return context

    filter_backends = [TypedCourseSearchBackend, CourseSearchFilterBackend]
    search_fields = ("full_code", "title", "sections__instructors__name")


class CourseDetail(generics.RetrieveAPIView, BaseCourseMixin):
    """
    Retrieve a detailed look at a specific course. Includes all details necessary to display course
    info, including requirements this class fulfills, and all sections.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("courses-detail", args=["semester", "full_code"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            reverse_func("courses-detail", args=["semester", "full_code"]): {
                "GET": {"semester": SEMESTER_PARAM_DESCRIPTION}
            }
        },
    )

    serializer_class = CourseDetailSerializer
    lookup_field = "full_code"
    queryset = Course.with_reviews.all()  # included redundantly for docs

    def get_queryset(self):
        queryset = Course.with_reviews.all()
        queryset = queryset.prefetch_related(
            Prefetch(
                "sections",
                Section.with_reviews.all()
                .filter(credits__isnull=False)
                .filter(Q(status="O") | Q(status="C"))
                .distinct()
                .prefetch_related(
                    "course", "meetings", "associated_sections", "meetings__room", "instructors"
                ),
            )
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class PreNGSSRequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of all pre-NGSS (deprecated since 2022C) academic requirements
    in the database for this semester.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("requirements-list", args=["semester"]): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Requirements listed successfully."}
            },
        },
        custom_path_parameter_desc={
            reverse_func("requirements-list", args=["semester"]): {
                "GET": {
                    "semester": (
                        "The semester of the requirement (of the form YYYYx where x is A "
                        "[for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019. "
                        "We organize requirements by semester so that we don't get huge related "
                        "sets which don't give particularly good info."
                    )
                }
            }
        },
    )

    serializer_class = PreNGSSRequirementListSerializer
    queryset = PreNGSSRequirement.objects.all()


class AttributeList(generics.ListAPIView):
    """
    Retrieve a list of unique attributes (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("attributes-list"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Attributes listed successfully."}
            },
        },
    )

    serializer_class = AttributeListSerializer
    queryset = Attribute.objects.all()


class NGSSRestrictionList(generics.ListAPIView):
    """
    Retrieve a list of unique restrictions (introduced post-NGSS)
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("restrictions-list"): {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Restrictions listed successfully."}
            },
        },
    )

    serializer_class = NGSSRestrictionListSerializer
    queryset = NGSSRestriction.objects.all()


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    This view exposes the Penn Labs Accounts User object.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def get_object(self):
        return self.request.user


class StatusUpdateView(generics.ListAPIView):
    """
    Retrieve all Status Update objects from the current semester for a specific section.
    """

    schema = PcxAutoSchema(
        response_codes={
            reverse_func("statusupdate", args=["full_code"]): {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Status Updates for section listed successfully."
                }
            }
        },
        custom_path_parameter_desc={
            reverse_func("statusupdate", args=["full_code"]): {
                "GET": {
                    "full_code": (
                        "The code of the section which this status update applies to, in the "
                        "form '{dept code}-{course code}-{section code}', e.g. `CIS-120-001` for "
                        "the 001 section of CIS-120."
                    )
                }
            }
        },
    )
    serializer_class = StatusUpdateSerializer
    http_method_names = ["get"]
    lookup_field = "section__full_code"

    def get_queryset(self):
        return StatusUpdate.objects.filter(
            section__full_code=self.kwargs["full_code"],
            section__course__semester=get_current_semester(),
            in_add_drop_period=True,
        ).order_by("created_at")


# private helper function used to get user's accepted friends
def get_accepted_friends(user):
    friendships = Friendship.objects.filter(Q(sender=user) | Q(recipient=user))
    accepted_friendships = friendships.filter(status=Friendship.FriendshipStatus.ACCEPTED)
    return [model_to_dict(friendship) for friendship in accepted_friendships]

class FriendshipViewSet(viewsets.ViewSet):
    model = Friendship
    queryset = Friendship.objects.all()
    http_method_names = ["get", "post", "delete"]
    permission_classes = [IsAuthenticated]

    # TODO: generate proper PcxAutoschema for this viewset
    schema = PcxAutoSchema()

    def get(self, request):
        # get user's friends and friend requests
        res = {}
        user = request.user

        friendships = self.queryset.filter(Q(sender=user) | Q(recipient=user))
        accepted_friendships = friendships.filter(status=Friendship.FriendshipStatus.ACCEPTED)
        pending_friendships = friendships.filter(status=Friendship.FriendshipStatus.SENT)
        rejected_friendships = friendships.filter(status=Friendship.FriendshipStatus.REJECTED)
        res["accepted"] = [model_to_dict(friendship) for friendship in accepted_friendships]
        res["pending"] = [model_to_dict(friendship) for friendship in pending_friendships]
        res["rejected"] = [
            model_to_dict(friendship) for friendship in rejected_friendships
        ]  # unsure if we should include this
        res["message"] = "Friendships retrieved successfully."
        return JsonResponse(res)
                
    def post(self, request):
        res = {}
        # send friendship request to passed in recipient
        sender = request.user
        recipient = get_object_or_404(User, id=request.recipient_id)

        if not recipient:
            res["message"] = "Recipient does not exist."
            return JsonResponse(res, status=400)

        # if friend request already exists but was rejected, we can reinstate it:
        friend_req = self.queryset.get(sender=sender, recipient=recipient, status=Friendship.FriendshipStatus.REJECTED)
        if not friend_req:
            friend_req = self.queryset.get(sender=recipient, recipient=sender, status=Friendship.FriendshipStatus.REJECTED)
        if friend_req:
            friend_req.status = Friendship.FriendshipStatus.SENT
            friendship.save()
            res = model_to_dict(friendship)
            res["message"] = "Friendship request sent successfully."
        
        if self.queryset.get(sender=sender, recipient=recipient, status=Friendship.FriendshipStatus.SENT).exists():
            res["message"] = "Friendship request already exists."
            return JsonResponse(res, status=status.HTTP_409_CONFLICT)

        # if a request exists in the other direction, then we accept the friend request
        friendship_request = self.queryset.get(sender=recipient, recipient=sender, status=Friendship.FriendshipStatus.SENT)
        if friendship_request:
            # accept friend request
            friendship_request.setStatus("A")
            friendship.save()
            res = model_to_dict(friendship_request)
            res["message"] = "Friendship request accepted."
        else:
            # create the friendship request
            friendship = Friendship(sender=sender, recipient=recipient)
            friendship.status = Friendship.FriendshipStatus.SENT
            friendship.save()
            res = model_to_dict(friendship)
            res["message"] = "Friendship request sent successfully."

        return JsonResponse(res, status=200)

    def delete(self, request):
        # either deletes a friendship or cancels a friendship request (depends on status)
        res = {}
        sender = request.user
        recipient = get_object_or_404(User, id=request.recipient_id)

        if not recipient:
            res["message"] = "Recipient does not exist."
            return JsonResponse(res, status=400)

        # delete the friendship/request (see if it exists the other way around)
        friendship = self.queryset.get(sender=sender, recipient=recipient)
        if not friendship:
            friendship = self.queryset.get(sender=recipient, recipient=sender)
        if not friendship:
            res["message"] = "Friendship/friendship request does not exist."
        else:
            friendship.delete()
            res["message"] = "Friendship request removed."
        return JsonResponse(res, status=200)
    
    # not sure what URL this method gets assigned to???
    def handle(self, request):
        res = {}
        # verify that the friendship request can be handled (only if it exists)
        # note that recipient is the only user that can handle a friendship request
        recipient = request.user
        sender = get_object_or_404(User, id=request.recipient_id)

        if not sender:
            res["message"] = "Friendship sender does not exist."
            return JsonResponse(res, status=400)

        friendship = self.queryset.get(sender=sender, recipient=recipient)
        if not friendship:
            res["message"] = "Friendship request does not exist."
        else:
            # handle the friendship request
            friendship.status = request.status
            friendship.save()
            res = model_to_dict(friendship)
            res["message"] = "Friendship request handled."
        return JsonResponse(res, status=200)
