import base64
import json
import logging

from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_auto_prefetching import AutoPrefetchViewSetMixin
from options.models import get_bool
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import alert.examples as examples

from alert.models import Registration, RegStatus, register_for_course
from alert.serializers import (
    RegistrationCreateSerializer,
    RegistrationSerializer,
    RegistrationUpdateSerializer,
)
from alert.tasks import send_course_alerts
from courses.util import get_current_semester, record_update, update_course_from_record
from PennCourses.docs_settings import PcxAutoSchema


logger = logging.getLogger(__name__)


def alert_for_course(c_id, semester, sent_by):
    send_course_alerts.delay(c_id, semester=semester, sent_by=sent_by)


def extract_basic_auth(auth_header):
    """
    extract username and password from a basic auth header
    :param auth_header: content of the Authorization HTTP header
    :return: username and password extracted from the header
    """
    parts = auth_header.split(" ")
    if parts[0] != "Basic" or len(parts) < 2:
        return None, None

    auth_parts = base64.b64decode(parts[1]).split(b":")
    if len(auth_parts) < 2:
        return None, None
    return auth_parts[0].decode(), auth_parts[1].decode()


@csrf_exempt
def accept_webhook(request):
    auth_header = request.META.get("Authorization", request.META.get("HTTP_AUTHORIZATION", ""))

    username, password = extract_basic_auth(auth_header)

    if username != settings.WEBHOOK_USERNAME or password != settings.WEBHOOK_PASSWORD:
        return HttpResponse(
            """Your credentials cannot be verified.
        They should be placed in the header as &quot;Authorization-Bearer&quot;,
        YOUR_APP_ID and &quot;Authorization-Token&quot; , YOUR_TOKEN""",
            status=401,
        )

    if request.method != "POST":
        return HttpResponse("Methods other than POST are not allowed", status=405)

    if "json" not in request.content_type.lower():
        return HttpResponse("Request expected in JSON", status=415)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Error decoding JSON body", status=400)

    course_id = data.get("course_section", None)
    if course_id is None:
        return HttpResponse("Course ID could not be extracted from response", status=400)

    course_status = data.get("status", None)
    if course_status is None:
        return HttpResponse("Course Status could not be extracted from response", status=400)

    course_term = data.get("term", None)
    if course_term is None:
        return HttpResponse("Course Term could not be extracted from response", status=400)

    prev_status = data.get("previous_status", None)
    if prev_status is None:
        return HttpResponse("Previous Status could not be extracted from response", status=400)

    should_send_alert = (
        get_bool("SEND_FROM_WEBHOOK", False)
        and course_status == "O"
        and get_current_semester() == course_term
    )

    alert_for_course_called = False
    if should_send_alert:
        try:
            alert_for_course(course_id, semester=course_term, sent_by="WEB")
            alert_for_course_called = True
            response = JsonResponse({"message": "webhook recieved, alerts sent"})
        except ValueError:
            response = JsonResponse({"message": "course code could not be parsed"})
    else:
        response = JsonResponse({"message": "webhook recieved"})

    try:
        u = record_update(
            course_id,
            course_term,
            prev_status,
            course_status,
            alert_for_course_called,
            request.body,
        )

        update_course_from_record(u)
    except ValueError as e:
        logger.error(e)
        return HttpResponse("We got an error but webhook should ignore it", status=200)

    return response


class RegistrationViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    retrieve: Get one of the logged-in user's PCA registrations for the current semester, using
    the registration's ID. Note that if a registration with the specified ID exists, but that
    registration is not at the head of its resubscribe chain (i.e. there is a more recent
    registration which was created by resubscribing to the specified registration), the
    HEAD of the resubscribe chain will be returned.  This may lead to unintuitive behavior, i.e.
    the same registration being returned from a GET request to 2 distinct IDs.
    If a registration with the specified ID exists, a 200 response code is
    returned, along with the head registration object.
    If the given id does not exist, a 404 is returned.

    list: Returns all registrations which are not deleted or made obsolete by resubscription.  Put
    another way, this endpoint will return a superset of all active registrations: all
    active registrations (meaning they would trigger an alert to be sent if their section
    were to open up), IN ADDITION TO all cancelled registrations from the current semester at
    the head of their resubscribe chains.  Each object in the returned list of registrations
    is of the same form as the object returned by Retrieve Registration.

    create: Use this route to create a PCA registration for a certain section.  A PCA registration
    represents a "subscription" to receive alerts for that section.  The body of the request must
    include a section field (with the dash-separated full code of the section) and optionally
    can contain an auto_resubscribe field (defaults to false) which sets whether the registration
    will automatically create a new registration once it triggers an alerts (i.e. whether it will
    automatically resubscribe the user to receive alerts for that section).  This route returns
    a 201 if the registration is successfully created, a 400 if the input is invalid
    (for instance if a null section is given), a 404 if the given section is not found in the
    database, a 406 if the authenticated user does not have either a phone or an email set
    in their profile (thus making it impossible for them to receive alerts), and a 409 if the
    user is already currently registered to receive alerts for the given section.

    update: test update description

    """

    schema = PcxAutoSchema(
        examples=examples.RegistrationViewSet_examples,
        response_codes={
            "/api/alert/registrations/": {
                "POST": {
                    201: "[SCHEMA]Registration successfully created.",
                    400: "Bad request (e.g. given null section).",
                    404: "Given section not found in database.",
                    406: "No contact information (phone or email) set for user.",
                    409: "Registration for given section already exists.",
                },
                "GET": {
                    200: "[SCHEMA]Registrations successfully listed."
                }
            },
            "/api/alert/registrations/{id}/": {
                "PUT": {
                    200: "Registration successfully updated (or no changes necessary).",
                    400: "Bad request (see route description)."
                },
                "GET": {
                    200: "[SCHEMA]Registration detail successfully retrieved."
                }
            }
        },
        override_schema=examples.RegistrationViewSet_override_schema
    )
    http_method_names = ["get", "post", "put"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return RegistrationCreateSerializer
        elif self.action == "update":
            return RegistrationUpdateSerializer
        else:
            return RegistrationSerializer

    @staticmethod
    def handle_registration(request):
        if not get_bool("REGISTRATION_OPEN", True):
            return Response(
                {"message": "Registration is not open."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        section_code = request.data.get("section", None)

        if section_code is None:
            return Response(
                {"message": "You must include a not null section"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        res, normalized_course_code, reg = register_for_course(
            course_code=section_code,
            source="PCA",
            user=request.user,
            auto_resub=request.data.get("auto_resubscribe", False),
        )

        if res == RegStatus.SUCCESS:
            return Response(
                {
                    "message": "Your registration for %s was successful!" % normalized_course_code,
                    "id": reg.pk,
                },
                status=status.HTTP_201_CREATED,
            )
        elif res == RegStatus.OPEN_REG_EXISTS:
            return Response(
                {
                    "message": "You've already registered to get alerts for %s!"
                    % normalized_course_code
                },
                status=status.HTTP_409_CONFLICT,
            )
        elif res == RegStatus.COURSE_NOT_FOUND:
            return Response(
                {
                    "message": "%s did not match any course in our database. Please try again!"
                    % section_code
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        elif res == RegStatus.NO_CONTACT_INFO:
            return Response(
                {
                    "message": "You must set a phone number and/or an email address to "
                    "register for an alert."
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        else:
            return Response(
                {"message": "There was an error on our end. Please try again!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset_current()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object().get_most_current_rec()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, pk=None):
        try:
            registration = self.get_queryset().get(id=pk)
        except Registration.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        registration = registration.get_most_current_rec()

        if registration.section.semester != get_current_semester():
            return Response(
                {"detail": "You can only update registrations from the current semester."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if request.data.get("resubscribe", False):
                if registration.deleted:
                    return Response(
                        {"detail": "You cannot resubscribe to a deleted registration."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not registration.notification_sent and not registration.cancelled:
                    return Response(
                        {
                            "detail": "You can only resubscribe to a registration that "
                            "has already been sent or has been cancelled."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                resub = registration.resubscribe()
                return Response(
                    {"detail": "Resubscribed successfully", "id": resub.id},
                    status=status.HTTP_200_OK,
                )
            elif request.data.get("deleted", False):
                changed = not registration.deleted
                registration.deleted = True
                registration.save()
                if changed:  # else taken care of in generic return statement
                    registration.deleted_at = timezone.now()
                    registration.save()
                    return Response({"detail": "Registration deleted"}, status=status.HTTP_200_OK)
            elif request.data.get("cancelled", False):
                if registration.deleted:
                    return Response(
                        {"detail": "You cannot cancel a deleted registration."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if registration.notification_sent:
                    return Response(
                        {"detail": "You cannot cancel a sent registration."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                changed = not registration.cancelled
                registration.cancelled = True
                registration.save()
                if changed:  # else taken care of in generic return statement
                    registration.cancelled_at = timezone.now()
                    registration.save()
                    return Response({"detail": "Registration cancelled"}, status=status.HTTP_200_OK)
            elif "auto_resubscribe" in request.data:
                if registration.deleted:
                    return Response(
                        {"detail": "You cannot make changes to a deleted registration."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                changed = registration.auto_resubscribe != request.data.get("auto_resubscribe")
                registration.auto_resubscribe = request.data.get("auto_resubscribe")
                registration.save()
                if changed:  # else taken care of in generic return statement
                    return Response(
                        {
                            "detail": "auto_resubscribe updated to "
                            + str(registration.auto_resubscribe)
                        },
                        status=status.HTTP_200_OK,
                    )
        except IntegrityError as e:
            return Response(
                {
                    "detail": "IntegrityError encountered while trying to update: "
                    + str(e.__cause__)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "no changes made"}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        if self.get_queryset().filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))
        return self.handle_registration(request)

    queryset = Registration.objects.none()  # used to help out the AutoSchema in generating documentation
    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)

    def get_queryset_current(self):
        """
        Returns a superset of all active registrations (also includes cancelled registrations
        from the current semester at the head of their resubscribe chains).
        """
        return Registration.objects.filter(
            user=self.request.user,
            deleted=False,
            resubscribed_to__isnull=True,
            section__course__semester=get_current_semester(),
        )


class RegistrationHistoryViewSet(AutoPrefetchViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    list:
    List all registrations for the current semester
    retrieve:

    """

    schema = PcxAutoSchema()
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    queryset = Registration.objects.none()  # used to help out the AutoSchema in generating documentation
    def get_queryset(self):
        return Registration.objects.filter(
            user=self.request.user, section__course__semester=get_current_semester()
        ).prefetch_related("section")
