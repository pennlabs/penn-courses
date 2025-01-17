import base64
import json
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django_auto_prefetching import AutoPrefetchViewSetMixin
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from alert.models import Registration, RegStatus, register_for_course
from alert.serializers import (
    RegistrationCreateSerializer,
    RegistrationSerializer,
    RegistrationUpdateSerializer,
)
from alert.tasks import send_course_alerts
from alert.util import pca_registration_open, should_send_pca_alert
from courses.util import (
    get_current_semester,
    get_or_create_course_and_section,
    record_update,
    translate_semester_inv,
    update_course_from_record,
)
from PennCourses.docs_settings import PcxAutoSchema


logger = logging.getLogger(__name__)


def alert_for_course(c_id, semester, sent_by, course_status):
    send_course_alerts.delay(c_id, course_status=course_status, semester=semester, sent_by=sent_by)


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
        logger.error("Credentials could not be verified")
        return HttpResponse(
            """Your credentials cannot be verified.
        They should be placed in the header as &quot;Authorization-Bearer&quot;,
        YOUR_APP_ID and &quot;Authorization-Token&quot; , YOUR_TOKEN""",
            status=200,
        )

    if request.method != "POST":
        logger.error("Methods other than POST are not allowed")
        return HttpResponse("Methods other than POST are not allowed", status=405)

    if "json" not in request.content_type.lower():
        logger.error("Request expected in JSON")
        return HttpResponse("Request expected in JSON", status=415)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Error decoding JSON body")
        return HttpResponse("Error decoding JSON body", status=400)

    course_id = data.get("section_id_normalized", None)
    if course_id is None:
        logger.error("Course ID could not be extracted from response")
        return HttpResponse("Course ID could not be extracted from response", status=400)

    course_status = data.get("status", None)
    if course_status is None:
        logger.error("Course Status couldn't be extracted from resp.")
        return HttpResponse("Course Status could not be extracted from response", status=400)

    prev_status = data.get("previous_status", None) or ""

    try:
        course_term = data.get("term", None)
        if course_term is None:
            logger.error("Course Term couldn't be extracted from resp.")
            return HttpResponse("Course Term could not be extracted from response", status=400)
        if any(course_term.endswith(s) for s in ["10", "20", "30"]):
            course_term = translate_semester_inv(course_term)
        if course_term.upper().endswith("B"):
            logger.error("webhook ignored (summer class)")
            return JsonResponse({"message": "webhook ignored (summer class)"})

        _, section, _, _ = get_or_create_course_and_section(course_id, course_term)

        # Ignore duplicate updates
        last_status_update = section.last_status_update
        if last_status_update and last_status_update.new_status == course_status:
            raise ValidationError(
                f"Status update received changing section {section} from "
                f"{prev_status} to {course_status}, "
                f"after previous status update from {last_status_update.old_status} "
                f"to {last_status_update.new_status} (duplicate or erroneous).",
            )
        elif last_status_update:
            logger.error(
                f"{section}: {prev_status} -> {course_status} "
                f"(last: {last_status_update.old_status} -> "
                f"{last_status_update.new_status})"
            )
        else:
            logger.error(f"{section}: {prev_status} -> {course_status} (no last)")

        alert_for_course_called = False
        if should_send_pca_alert(course_term, course_status):
            try:
                alert_for_course(
                    course_id, semester=course_term, sent_by="WEB", course_status=course_status
                )
                alert_for_course_called = True
                response = JsonResponse({"message": "webhook recieved, alerts sent"})
            except ValueError:
                logger.error("course code could not be parsed")
                response = JsonResponse({"message": "course code could not be parsed"})
        else:
            response = JsonResponse({"message": "webhook recieved"})

        with transaction.atomic():
            u = record_update(
                section,
                course_term,
                prev_status,
                course_status,
                alert_for_course_called,
                request.body,
            )
            update_course_from_record(u)
    except (ValidationError, ValueError) as e:
        logger.error(e, extra={"request": request})
        response = JsonResponse(
            {"message": "We got an error but webhook should ignore it"}, status=200
        )

    return response


class RegistrationViewSet(AutoPrefetchViewSetMixin, viewsets.ModelViewSet):
    """
    retrieve: Get one of the logged-in user's PCA registrations for the current semester, using
    the registration's ID. Note that if a registration with the specified ID exists, but that
    registration is not at the head of its resubscribe chain (i.e. there is a more recent
    registration which was created by resubscribing to the specified registration), the
    HEAD of the resubscribe chain will be returned.  This means the same registration could be
    returned from a GET request to 2 distinct IDs (if they are in the same resubscribe chain).
    If a registration with the specified ID exists, a 200 response code is returned, along
    with the head registration object. If no registration with the given id exists,
    a 404 is returned.

    list: Returns all registrations which are not deleted or made obsolete by resubscription.  Put
    another way, this endpoint will return a superset of all active registrations: all
    active registrations (meaning registrations which would trigger an alert to be sent if their
    section were to open up), IN ADDITION TO all inactive registrations from the current semester
    which are at the head of their resubscribe chains and not deleted.  However, one extra
    modification is made: if multiple registrations for the same section are included in the
    above-specified set, then all but the most recent (latest `created_at` value) are removed from
    the list. This ensures that at most 1 registration is returned for each section. Note that this
    is still a superset of all active registrations. If a registration is active, its `created_at`
    value will be greater than any other registrations for the same section (our code ensures no
    registration can be created or resubscribed to when an active registration exists for the same
    section). This extra modification is actually made to prevent the user from being able to
    resubscribe to an older registration after creating a new one (which would cause the backend to
    return a 409 error).

    Each object in the returned list of registrations is of the same form as the object returned
    by Retrieve Registration.

    Tip: if you sort this list by `original_created_at` (the `created_at` value of the tail of
    a registration's resubscribe chain), cancelling or resubscribing to registrations will
    not cause the registration to jump to a different place in the list (which makes for
    more intuitive/understandable behavior for the user if the registrations are displayed
    in that order). This is what PCA currently does on the manage alerts page.

    create: Use this route to create a PCA registration for a certain section.  A PCA registration
    represents a "subscription" to receive alerts for that section.  The body of the request must
    include a section field (with the dash-separated full code of the section) and optionally
    can contain an auto_resubscribe field (defaults to false) which sets whether the registration
    will automatically create a new registration once it triggers an alerts (i.e. whether it will
    automatically resubscribe the user to receive alerts for that section). It can also optionally
    contain a "close_notification" field, to enable close notifications on the registration.
    Note that close notifications CANNOT be sent by text so you shouldn't allow the user to
    enable close notifications for any registration unless they have an email set in their
    User Profile or have push notifications enabled.  If you try to create a registration with
    close_notification enabled and the user only has texts enabled, , a 406 will be returned
    and the registration will not be created.
    Note that if you include the "id" field in the body of your POST request, and that id
    does not already exist, the id of the created registration will be set to the given value.
    However, if the given id does exist, the request will instead be treated as a PUT request for
    the registration (see the Update Registration docs for more info on how
    PUT requests are handled).

    This route returns a 201 if the registration is successfully created, a 400 if the input is
    invalid (for instance if a null section is given), a 404 if the given section is not found in
    the database, a 406 if the authenticated user does not have either a phone or an email set
    in their profile (thus making it impossible for them to receive alerts), and a 409 if the
    user is already currently registered to receive alerts for the given section.  If the request
    is redirected to update (when the passed in id is already associated with a registration),
    other response codes may be returned (see the Update Registration docs for more info). If
    registration is not currently open on PCA, a 503 is returned.

    update: Use this route to update existing PCA Registrations.  Note that the provided id does
    not always strictly specify which Registration gets modified.  In fact, the actual Registration
    that would get modified by a PUT request would be the head of the resubscribe chain of the
    Registration with the specified id (so if you try to update an outdated Registration it will
    instead update the most recent Registration).  The parameters which can be
    included in the request body are `resubscribe`, `auto_resubscribe`, 'close_notification',
    `cancelled`, and `deleted`. If you include multiple parameters, the order of precedence in
    choosing what action to take is `resubscribe` > `deleted` > `cancelled` >
    [`auto_resubscribe` and `close_notification`] (so if you include multiple
    parameters only the action associated with the highest priority parameter will be executed,
    except both auto_resubscribe and close_notification can be updated in the same request).
    Note that close notifications CANNOT be sent by text so you shouldn't allow the user to
    enable close notifications for any registration unless they have an email set in their
    User Profile or have push notifications enabled.  If you try to update a registration to
    enable close_notification and the user only has texts enabled, a 406 will be returned
    and the registration will not be created.
    Note that a registration will send an alert when the section it is watching opens, if and only
    if it hasn't sent one before, it isn't cancelled, and it isn't deleted.  If a registration would
    send an alert when the section it is watching opens, we call it "active".  Registrations which
    have triggered an alert can be resubscribed to (which creates a new registration with the same
    settings and adds that to the end of the original registration's resubscribe chain).  Triggered
    registrations would show up in List Registrations (as long as they are at the head of
    their resubscribe chain), even though they aren't active.  Cancelled registrations can also
    be resubscribed to (in effect uncancelling), and also show up in List Registrations, despite
    not being active.  A user might cancel an alert rather than delete it if they want to keep it
    in their PCA manage console but don't want to receive alerts for it.  Deleted registrations
    are not active, do not show up in List Registrations, and cannot be resubscribed to.  You can
    think of deleted registrations as effectively nonexistent; they are only kept on the backend
    for analytics purposes.  Note that while you can cancel a registration by setting the cancelled
    parameter to true in your PUT request (and the same for delete/deleted), you cannot uncancel
    or undelete (cancelled registrations can be resubscribed to and deleted registrations
    are effectively nonexistent).

    If the update is successful, a 200 is returned.  If there is some issue with the request,
    a 400 is returned.  This could be caused by trying to update a registration from a different
    semester, trying to resubscribe to a deleted registration, resubscribing to a registration
    which is not cancelled or hasn't yet triggered a notification, cancelling a deleted or
    triggered registration, trying to make changes to a deleted registration, or otherwise
    breaking rules.  Look in the detail field of the response object for more detail on what
    exactly went wrong if you encounter a 400.  If no registration with the given id is found,
    a 404 is returned. If registration is not currently open on PCA, a 503 is returned.
    """

    schema = PcxAutoSchema(
        response_codes={
            "registrations-list": {
                "POST": {
                    201: "[DESCRIBE_RESPONSE_SCHEMA]Registration successfully created.",
                    400: "Bad request (e.g. given null section).",
                    404: "Given section not found in database.",
                    406: "No contact information (phone or email) set for user.",
                    409: "Registration for given section already exists.",
                    503: "Registration not currently open.",
                },
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Registrations successfully listed."},
            },
            "registrations-detail": {
                "PUT": {
                    200: "Registration successfully updated (or no changes necessary).",
                    400: "Bad request (see route description).",
                    404: "Registration not found with given id.",
                    503: "Registration not currently open.",
                },
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Registration detail successfully retrieved.",
                    404: "Registration not found with given id.",
                },
            },
        },
        override_response_schema={
            "registrations-list": {
                "POST": {
                    201: {"properties": {"message": {"type": "string"}, "id": {"type": "integer"}}},
                }
            }
        },
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
        if not pca_registration_open():
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
            close_notification=request.data.get("close_notification", False),
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
        elif res == RegStatus.TEXT_CLOSE_NOTIFICATION:
            return Response(
                {
                    "message": "You can only enable close notifications on a registration if the "
                    "user enables some form of communication other than just texts (we don't "
                    "send any close notifications by text)."
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        else:
            return Response(
                {"message": "There was an error on our end. Please try again!"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset_current())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object().get_most_current()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, pk=None):
        if not Registration.objects.filter(id=pk).exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            try:
                registration = self.get_queryset().select_for_update().get(id=pk)
            except Registration.DoesNotExist:
                return Response(
                    {"detail": "You do not have access to the specified registration."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            registration = registration.get_most_current()

            if registration.section.semester != get_current_semester():
                return Response(
                    {"detail": "You can only update registrations from the current semester."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                if request.data.get("resubscribe", False):
                    if not pca_registration_open():
                        return Response(
                            {"message": "Registration is not open."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE,
                        )
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
                    if registration.section.registrations.filter(
                        user=registration.user, **Registration.is_active_filter()
                    ).exists():
                        # An active registration for this section already exists
                        return Response(
                            {
                                "message": "You've already registered to get alerts for %s!"
                                % registration.section.full_code
                            },
                            status=status.HTTP_409_CONFLICT,
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
                        return Response(
                            {"detail": "Registration deleted"}, status=status.HTTP_200_OK
                        )
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
                        return Response(
                            {"detail": "Registration cancelled"}, status=status.HTTP_200_OK
                        )
                elif "auto_resubscribe" in request.data or "close_notification" in request.data:
                    if registration.deleted:
                        return Response(
                            {"detail": "You cannot make changes to a deleted registration."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    auto_resubscribe_changed = registration.auto_resubscribe != request.data.get(
                        "auto_resubscribe", registration.auto_resubscribe
                    )
                    close_notification_changed = (
                        registration.close_notification
                        != request.data.get("close_notification", registration.close_notification)
                    )
                    if (
                        request.data.get("close_notification", registration.close_notification)
                        and not request.user.profile.email
                        and not request.user.profile.push_notifications
                    ):
                        return Response(
                            {
                                "detail": "You cannot enable close_notifications with only "
                                "your phone number saved in your user profile."
                            },
                            status=status.HTTP_406_NOT_ACCEPTABLE,
                        )
                    changed = auto_resubscribe_changed or close_notification_changed
                    registration.auto_resubscribe = request.data.get(
                        "auto_resubscribe", registration.auto_resubscribe
                    )
                    registration.close_notification = request.data.get(
                        "close_notification", registration.close_notification
                    )
                    registration.save()
                    if changed:  # else taken care of in generic return statement
                        return Response(
                            {
                                "detail": ", ".join(
                                    (
                                        [
                                            "auto_resubscribe updated to "
                                            + str(registration.auto_resubscribe)
                                        ]
                                        if auto_resubscribe_changed
                                        else []
                                    )
                                    + (
                                        [
                                            "close_notification updated to "
                                            + str(registration.close_notification)
                                        ]
                                        if close_notification_changed
                                        else []
                                    )
                                )
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
        if Registration.objects.filter(id=request.data.get("id")).exists():
            return self.update(request, request.data.get("id"))
        return self.handle_registration(request)

    queryset = Registration.objects.none()  # included redundantly for docs

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)

    def get_queryset_current(self):
        """
        Returns a superset of all active registrations (also includes cancelled registrations
        from the current semester at the head of their resubscribe chains). Returns at most 1
        registration per section (if multiple candidate registrations for a certain section exist,
        the registration with the later created_at value is chosen).
        """
        registrations = Registration.objects.filter(
            user=self.request.user,
            deleted=False,
            resubscribed_to__isnull=True,
            section__course__semester=get_current_semester(),
        )
        # Now resolve conflicts where multiple registrations exist for the same section
        # (by taking the registration with the later created_at date)
        return registrations.filter(
            created_at__in=registrations.values("section")
            .annotate(max_created_at=Max("created_at"))
            .values_list("max_created_at", flat=True)
        )


class RegistrationHistoryViewSet(AutoPrefetchViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    list:
    List all of the user's registrations for the current semester, regardless of whether
    they are active, obsolete (not at the head of their resubscribe chains), or deleted.  Note
    that this is not appropriate to use for listing registrations and presenting them to the user;
    for that you should use List Registrations (GET `/api/alert/registrations/`).
    retrieve:
    Get the detail of a specific registration from the current semester.  All registrations are
    accessible via this endpoint, regardless of whether they are active,
    obsolete (not at the head of their resubscribe chains), or deleted.  Unless you need to access
    inactive and obsolete registrations, you should probably use Retrieve Registration
    (GET `/api/alert/registrations/{id}/`) rather than this endpoint.
    """

    schema = PcxAutoSchema(
        response_codes={
            "registrationhistory-list": {
                "GET": {200: "[DESCRIBE_RESPONSE_SCHEMA]Registration history successfully listed."}
            },
            "registrationhistory-detail": {
                "GET": {
                    200: "[DESCRIBE_RESPONSE_SCHEMA]Historic registration detail "
                    "successfully retrieved.",
                    404: "Historic registration not found with given id.",
                }
            },
        },
    )
    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    queryset = Registration.objects.none()  # included redundantly for docs

    def get_queryset(self):
        return Registration.objects.filter(
            user=self.request.user, section__course__semester=get_current_semester()
        ).prefetch_related("section")
