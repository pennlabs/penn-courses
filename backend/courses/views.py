from textwrap import dedent

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses.filters import CourseSearchFilterBackend
from courses.models import (
    Attribute,
    Course,
    Friendship,
    NGSSRestriction,
    PreNGSSRequirement,
    Section,
    StatusUpdate,
    User,
)
from courses.search import TypedCourseSearchBackend, TypedSectionSearchBackend
from courses.serializers import (
    AttributeListSerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    FriendshipSerializer,
    MiniSectionSerializer,
    NGSSRestrictionListSerializer,
    PreNGSSRequirementListSerializer,
    SectionDetailSerializer,
    StatusUpdateSerializer,
    UserSerializer,
)
from courses.util import get_current_semester
from PennCourses.docs_settings import PcxAutoSchema
from plan.management.commands.recommendcourses import retrieve_course_clusters, vectorize_user


SEMESTER_PARAM_DESCRIPTION = (
    "The semester of the course (of the form YYYYx where x is A [for spring], "
    "B [summer], or C [fall]), e.g. '2019C' for fall 2019. Alternatively, you "
    "can just pass 'current' for the current semester. Finally, you can pass 'all' "
    "to always return the most recent course for each full_code, no matter which "
    "semester it is from. The 'all' option can be significantly more expensive, so use "
    "only where needed. "
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
        else:  # Only used for Penn Degree Plan (as of 4/10/2024)
            queryset = (
                queryset.exclude(credits=None)  # heuristic: if the credits are empty, then ignore
                .order_by("full_code", "-semester")
                .distinct("full_code")
            )
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
            "section-search": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Sections Listed Successfully."}
            }
        },
        custom_path_parameter_desc={
            "section-search": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
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
            "sections-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Section detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            "sections-detail": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
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
            "courses-list": {"GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully."}}
        },
        custom_path_parameter_desc={
            "courses-list": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
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
            "courses-search": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Courses listed successfully.",
                    400: "Bad request (invalid query).",
                }
            }
        },
        custom_path_parameter_desc={
            "courses-search": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
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
            "courses-detail": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Courses detail retrieved successfully."}
            }
        },
        custom_path_parameter_desc={
            "courses-detail": {"GET": {"semester": SEMESTER_PARAM_DESCRIPTION}}
        },
        custom_parameters={
            "courses-detail": {
                "GET": [
                    {
                        "name": "check_offered_in",
                        "in": "query",
                        "description": dedent(
                            """
                            Check that the desired course was offered under the specified
                            code in the specified semester.
                            Format is `course_code@semester`, e.g. `CIS-1210@2022A`.
                            404 will be returned if the course
                            does not exist, or was not offered in that semester.
                            """
                        ),
                        "schema": {"type": "string"},
                        "required": False,
                    }
                ]
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
                    "course",
                    "meetings",
                    "associated_sections",
                    "meetings__room",
                    "instructors",
                ),
            )
        )
        check_offered_in = self.request.query_params.get("check_offered_in")
        if check_offered_in:
            if "@" not in check_offered_in:
                raise ValidationError(
                    "check_offered_in expects an argument of the form `CIS-1210@2022C`."
                )
            check_offered_in = check_offered_in.split("@")
            if len(check_offered_in) != 2:
                raise ValidationError(
                    "check_offered_in expects an argument of the form `CIS-1210@2022C`."
                )
        queryset = (
            queryset.filter(
                topic__courses__full_code=check_offered_in[0],
                topic__courses__semester=check_offered_in[1],
            )
            if check_offered_in
            else queryset
        )
        queryset = self.filter_by_semester(queryset)
        return queryset


class PreNGSSRequirementList(generics.ListAPIView, BaseCourseMixin):
    """
    Retrieve a list of all pre-NGSS (deprecated since 2022B) academic requirements
    in the database for this semester.
    """

    schema = PcxAutoSchema(
        response_codes={
            "requirements-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Requirements listed successfully."}
            },
        },
        custom_path_parameter_desc={
            "requirements-list": {
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
            "attributes-list": {
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
            "restrictions-list": {
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
            "statusupdate": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Status Updates for section listed successfully."
                }
            }
        },
        custom_path_parameter_desc={
            "statusupdate": {
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


def get_accepted_friends(user):
    """Return user's accepted friends"""
    return User.objects.filter(
        received_friendships__sender=user, received_friendships__status=Friendship.Status.ACCEPTED
    ) | User.objects.filter(
        sent_friendships__recipient=user, sent_friendships__status=Friendship.Status.ACCEPTED
    )


class FriendshipView(generics.ListAPIView):
    """
    get: Get a list of all friendships and friendship requests (sent and recieved) for the
    specified user. Filter the list by status (accepted, sent) to distinguish between
    friendships and friendship requests.

    post: Create a friendship between two users (sender and recipient). If a previous request does
    not exist between the two friendships, then we create friendship request. If a previous request
    exists (where the recipient is the sender) and the recipient of a request hits this route, then
    we accept the request.

    delete: Delete a friendship between two users (sender and recipient). If there exists only
    a friendship request between two users, then we either delete the friendship request
    if the sender hits the route, or we reject the request if the recipient hits this route.
    """

    #  model = Friendship
    serializer_class = FriendshipSerializer
    http_method_names = ["get", "post", "delete"]
    permission_classes = [IsAuthenticated]

    schema = PcxAutoSchema(
        response_codes={
            "friendship": {
                "GET": {
                    200: "Friendships retrieved successfully.",
                },
                "POST": {
                    201: "Friendship request created successfully.",
                    200: "Friendship request accepted successfully.",
                    409: "Friendship request already exists",
                },
                "DELETE": {
                    200: "Friendship rejected/deleted/cancelled successfully.",
                    404: "Friendship does not exist.",
                    409: "Friendship request already rejected.",
                },
            }
        },
        custom_parameters={
            "friendship": {
                "DELETE": [
                    {
                        "name": "pennkey",
                        "in": "query",
                        "description": "The Pennkey of the user you are ending/rejecting your friendship/friend request with.",  # noqa E501
                        "schema": {"type": "string"},
                        "required": True,
                    },
                ]
            },
        },
        override_request_schema={
            "friendship": {
                "POST": {
                    "type": "object",
                    "properties": {
                        "pennkey": {
                            "type": "string",
                            "description": "The Pennkey of the user you are sending a friend request to or handling a request from.",  # noqa E501
                            "required": True,
                        },
                    },
                }
            }
        },
    )

    # only returns accepted / sent friendships
    def get_queryset(self):
        return Friendship.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
            Q(status=Friendship.Status.ACCEPTED) | Q(status=Friendship.Status.SENT),
        )

    # returns all friendships (regardless of status)
    def get_all_friendships(self):
        return Friendship.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )

    def post(self, request):
        sender = request.user
        recipient = get_object_or_404(User, username=request.data.get("pennkey"))

        existing_friendship = (
            self.get_all_friendships().filter(Q(recipient=recipient) | Q(sender=recipient)).first()
        )

        if not existing_friendship:
            friendship = Friendship(
                sender=sender, recipient=recipient, status=Friendship.Status.SENT
            )
            friendship.save()
            res = FriendshipSerializer(friendship)
            return Response(data=res.data, status=status.HTTP_201_CREATED)
        elif existing_friendship.status == Friendship.Status.REJECTED:
            existing_friendship.status = Friendship.Status.SENT
            existing_friendship.sender = sender
            existing_friendship.recipient = recipient
            existing_friendship.save()
            res = FriendshipSerializer(existing_friendship)
            return Response(data=res.data, status=status.HTTP_200_OK)
        elif existing_friendship.status == Friendship.Status.SENT:
            if existing_friendship.sender == sender:
                return Response({}, status=status.HTTP_409_CONFLICT)
            elif existing_friendship.recipient == sender:
                existing_friendship.status = Friendship.Status.ACCEPTED
                existing_friendship.save()
                res = FriendshipSerializer(existing_friendship)
                return Response(res.data, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_409_CONFLICT)

    def delete(self, request):
        # either deletes a friendship or cancels/rejects a friendship request
        # (depends on who sends the request)
        res = {}
        sender = request.user
        recipient = get_object_or_404(User, username=request.data.get("pennkey"))

        existing_friendship = (
            self.get_all_friendships().filter(Q(recipient=recipient) | Q(sender=recipient)).first()
        )
        if not existing_friendship:
            res["message"] = "Friendship doesn't exist."
            return JsonResponse(res, status=status.HTTP_404_NOT_FOUND)

        if existing_friendship.status == Friendship.Status.ACCEPTED:
            existing_friendship.delete()
            res["message"] = "Friendship deleted successfully."
        elif existing_friendship.status == Friendship.Status.SENT:
            if existing_friendship.sender == sender:
                existing_friendship.delete()
                res["message"] = "Friendship request removed."
            if existing_friendship.recipient == sender:
                existing_friendship.status = Friendship.Status.REJECTED
                existing_friendship.save()
                res["message"] = "Friendship request rejected."
        else:
            res["message"] = "Friendship request already rejected."
            return JsonResponse(res, status=status.HTTP_409_CONFLICT)
        return JsonResponse(res, status=status.HTTP_200_OK)
