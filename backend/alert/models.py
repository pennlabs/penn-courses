import logging
from contextlib import nullcontext
from datetime import datetime
from enum import Enum, auto
from textwrap import dedent

import phonenumbers  # library for parsing and formatting phone numbers.
import pytz
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.db.models import Case, F, Max, Q, Value, When
from django.utils import timezone
from django.utils.timezone import make_aware

from alert.alerts import Email, PushNotification, Text
from courses.models import Course, Section, StatusUpdate, UserProfile, string_dict_to_html
from courses.util import get_course_and_section, get_current_semester
from PennCourses.settings.base import TIME_ZONE


class RegStatus(Enum):
    SUCCESS = auto()
    OPEN_REG_EXISTS = auto()
    COURSE_OPEN = auto()
    COURSE_NOT_FOUND = auto()
    NO_CONTACT_INFO = auto()
    TEXT_CLOSE_NOTIFICATION = auto()


SOURCE_PCA = "PCA"
SOURCE_API = "API"


class Registration(models.Model):
    """
    A registration for sending an alert to the user upon the opening of a course
    during open registration.

    In addition to sending alerts for when a class opens up, we have also implemented
    an optionally user-enabled feature called "close notifications".
    If a registration has close_notification enabled, it will act normally when the watched
    section opens up for the first time (triggering an alert to be sent). However, once the
    watched section closes, it will send another alert (the email alert will be in the same
    chain as the original alert) to let the user know that the section has closed. Thus,
    if a user sees a PCA notification on their phone during a class for instance, they won't
    need to frantically open up their laptop and check PennInTouch to see if the class is still
    open just to find that it is already closed.  To avoid spam and wasted money, we DO NOT
    send any close notifications over text. So the user must have an email saved or use
    push notifications in order to be able to enable close notifications on a registration.
    Note that the close_notification setting carries over across resubscriptions, but can be
    disabled at any time using a PUT request to /api/alert/registrations/{id}/.

    An important concept for this Model is that of the "resubscribe chain".  A resubscribe chain
    is a chain of Registration objects where the tail of the chain was the original Registration
    created through a POST request to /api/alert/registrations/ specifying a new section (one
    that the user wasn't already registered to receive alerts for).  Each next element in the chain
    is a Registration created by resubscribing to the previous Registration (once that
    Registration had triggered an alert to be sent), either manually by the user or
    automatically if auto_resubscribe was set to true.  Then, it follows that the head of the
    resubscribe chain is the most relevant Registration for that user/section combo; if any
    of the registrations in the chain are active, it would be the head.  And if the head
    is active, none of the other registrations in the chain are active.  That said, a non-head
    Registration may be waiting to send a close notification (if the watched section hasn't closed
    yet).

    Note that a Registration will send an alert when the section it is watching opens, if and
    only if it hasn't sent one before, it isn't cancelled, and it isn't deleted.  If a
    registration would send an alert when the section it is watching opens, we call it
    "active".  This rule is encoded in the is_active property.  You can also filter
    for active registrations by unpacking the static is_active_filter() method which returns a
    dictionary that you can unpack into the kwargs of the filter method
    (you cannot filter on a property). A Registration will send a close notification
    when the section it is watching closes, if and only if it has already sent an open alert,
    the user has enabled close notifications for that section, the Registration hasn't sent a
    close_notification before, is not cancelled, and it is not deleted.  If a registration would
    send a close notification when the section it is watching closes, we call it "waiting for
    close".  This rule is encoded in the is_waiting_for_close property.  You can also filter
    for such registrations by unpacking (with single *) the static is_waiting_for_close_filter()
    method which returns a tuple of Q filters (you cannot filter on a property).

    After the PCA backend refactor in 2019C/2020A, all PCA Registrations have a user field
    pointing to the user's Penn Labs Accounts User object.  In other words, we implemented a
    user/accounts system for PCA which required that
    people log in to use the website. Thus, the contact information used in PCA alerts
    is taken from the user's User Profile.  You can edit this contact information using
    a PUT or PATCH request to /accounts/me/.  If push_notifications is set to True, then
    a push notification will be sent when the user is alerted, but no text notifications will
    be sent (as that would be a redundant alert to the user's phone). Otherwise, an email
    or a text alert is sent if and only if contact information for that medium exists in
    the user's profile.

    Alerts are triggered by webhook requests from the UPenn OpenData API
    (https://esb.isc-seo.upenn.edu/8091/documentation/#coursestatuswebhookservice), and accepted
    by alert/views.py/accept_webhook. Then if the SEND_FROM_WEBHOOK Option is set to True,
    the semester of the webhook request equals courses.util.get_current_semester(), and the new
    course status is either "O" (meaning open) or "C" (meaning closed), the method calls
    alert/views.py/alert_for_course for the relevant course.  That method then calls
    alert/tasks.py/send_course_alerts asynchronously using the Celery delay function.
    This allows for alerts to be queued without holding up the response.  The send_course_alerts
    function then loops through all registrations for the given section and calls
    alert/tasks.py/send_alert asynchronously (again using Celery delay) which then calls the
    Registration's alert method. In each Registration's alert method, a subclass of the
    alert/alerts.py/Alert class is instantiated for each of the appropriate notification
    channels (text, email, and/or push notification based on the User's settings).  The
    notification is then sent with the send_alert method on each Alert object.  The send_alert
    method calls other functions in alert/alerts.py to actually send out the alerts.
    """

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The datetime at which this registration was created."
    )
    original_created_at = models.DateTimeField(
        null=True,
        help_text=dedent(
            """
        The datetime at which the tail of the resubscribe chain to which this registration belongs
        was created.  In other words, the datetime at which the user created the original
        registration for this section, before resubscribing some number of times
        (0 or more) to reach this registration.
        """
        ),
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="The datetime at which this registration was last modified."
    )

    SOURCE_CHOICES = (
        ("PCA", "Penn Course Alert"),
        ("API", "3rd Party Integration"),
        ("PCP", "Penn Course Plan"),
        ("PCR", "Penn Course Review"),
        ("PM", "Penn Mobile"),
        ("SCRIPT_PCN", "The loadregistrations_pcn shell command"),
        ("SCRIPT_PCA", "The loadregistrations_pca shell command"),
    )

    source = models.CharField(
        max_length=16,
        choices=SOURCE_CHOICES,
        help_text="Where did the registration come from? Options and meanings: "
        + string_dict_to_html(dict(SOURCE_CHOICES)),
    )

    api_key = models.ForeignKey(
        "courses.APIKey",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
        An API key for 3rd party alternatives to PCA. This is currently unused now that
        Penn Course Notify has fallen, but may be used in the future.
        """
        ),
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=dedent(
            """
        The User that registered for this alert. This object will be none if registration occurred
        before the PCA refresh of Spring 2020 (before the refresh user's were only identified by
        their email and phone numbers, which are legacy fields in this model now). This object
        might also be none if registration occurred through a 3rd part API such as Penn Course
        Notify (now that Notify has fallen this is an unlikely event).
        """
        ),
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        A legacy field that stored the user's email before the Spring 2020 PCA refresh. Currently,
        for all new registrations the email and phone fields will be None and contact information
        can be found in the User's UserProfile object (related_name is profile, so you can
        access the profile from the User object with `.user.profile`).
        """
        ),
    )
    phone = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        help_text=dedent(
            """
        A legacy field that stored the user's phone before the Spring 2020 PCA refresh. Currently,
        for all new registrations the email and phone fields will be None and contact information
        can be found in the User's UserProfile object (related_name is profile, so you can
        access the profile from the User object with `.user.profile`).
        """
        ),
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="registrations",
        help_text="The section that the user registered to be notified about.",
    )
    cancelled = models.BooleanField(
        default=False,
        help_text=dedent(
            """
        Defaults to False, changed to True if the registration has been cancelled. A cancelled
        registration will not trigger any alerts to be sent even if the relevant section opens.
        A cancelled section can be resubscribed to (unlike deleted alerts), and will show up
        on the manage alerts page on the frontend (also unlike deleted alerts). Note that once
        a registration is cancelled, it cannot be uncancelled (resubscribing creates a new
        registration which is accessible via the resubscribed_to field, related name of
        resubscribed_from).
        """
        ),
    )
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When was the registration cancelled? Null if it hasn't been cancelled.",
    )
    deleted = models.BooleanField(
        default=False,
        help_text=dedent(
            """
        Defaults to False, changed to True if the registration has been deleted. A deleted
        registration will not trigger any alerts to be sent even if the relevant section opens.
        A deleted section cannot be resubscribed to or undeleted, and will not show up on the
        manage alerts page on the frontend. It is kept in the database for analytics purposes,
        even though it serves no immediate functional purpose for its original user.
        """
        ),
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When was the registration deleted? Null if it hasn't been deleted.",
    )
    auto_resubscribe = models.BooleanField(
        default=False,
        help_text=dedent(
            """
        Defaults to False, in which case a registration will not be automatically resubscribed
        after it triggers an alert to be sent (but the user can still resubscribe to a sent alert,
        as long as it is not deleted). If set to True, the registration will be automatically
        resubscribed to once it triggers an alert to be sent (this is useful in the case of
        volatile sections which are opening and closing frequently, often before the user has
        time to register).
        """
        ),
    )
    notification_sent = models.BooleanField(
        default=False, help_text="True if an alert has been sent to the user, false otherwise."
    )
    notification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        When was an alert sent to the user as a result of this registration?
        Null if an alert was not sent.
        """
        ),
    )
    close_notification = models.BooleanField(
        default=False,
        help_text=dedent(
            """Defaults to False.  Changes to True if the user opts-in to receive
        a close notification (an alert when the section closes after an
        alert was sent for it opening).
        """
        ),
    )
    close_notification_sent = models.BooleanField(
        default=False,
        help_text="True if a close notification has been sent to the user, false otherwise.",
    )
    close_notification_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        When was a close notification sent to the user as a result of this registration?
        Null if a close notification was not sent.
        """
        ),
    )

    METHOD_CHOICES = (
        ("", "Unsent"),
        ("LEG", "[Legacy] Sequence of course API requests"),
        ("WEB", "Webhook"),
        ("SERV", "Course Status Service"),
        ("ADM", "Admin Interface"),
    )
    notification_sent_by = models.CharField(
        max_length=16,
        choices=METHOD_CHOICES,
        default="",
        blank=True,
        help_text="What triggered the alert to be sent? Options and meanings: "
        + string_dict_to_html(dict(METHOD_CHOICES)),
    )
    close_notification_sent_by = models.CharField(
        max_length=16,
        choices=METHOD_CHOICES,
        default="",
        blank=True,
        help_text="What triggered the close notification to be sent?  Options and meanings: "
        + string_dict_to_html(dict(METHOD_CHOICES)),
    )

    # track resubscriptions
    resubscribed_from = models.OneToOneField(
        "Registration",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="resubscribed_to",
        help_text=dedent(
            """
        The registration which was resubscribed to, triggering the creation of this registration.
        If this registration is the original registration in its resubscribe chain (the tail),
        this field is null. The related field, 'resubscribed_to' only exists as an attribute of
        a Registration object if the registration has been resubscribed. In that case,
        the field resubscribed_to will point to the next element in the resubscribe chain.
        If the field does not exist, this registration is the head of its resubscribe chain
        (note that an element can be both the head and the tail of its resubscribe chain,
        in which case it is the only element in its resubscribe chain).
        """
        ),
    )

    @staticmethod
    def is_active_filter():
        """
        Returns a dict of filters defining the behavior of the is_active property.
        Also used in database filtering of registrations (you cannot filter by a property value);
        unpack the filters with two stars (NOT a single star like is_waiting_for_close_filter).
        Example:
            Registration.objects.filter(**Registration.is_active_filter())
        """
        return {
            "notification_sent": False,
            "deleted": False,
            "cancelled": False,
        }

    @property
    def is_active(self):
        """
        True if the registration would send an alert when the watched section changes to open,
        False otherwise. This is equivalent to
        [not(notification_sent or deleted or cancelled) and semester is current].
        """
        for field, active_value in self.is_active_filter().items():
            assert field != ""  # this should never fail
            actual_value = getattr(self, field)
            if actual_value != active_value:
                return False
        return True

    @property
    def deactivated_at(self):
        """
        The datetime at which this registration was deactivated, if it is not active,
        otherwise None. This checks all fields in the is_active definition which have a
        corresponding field+"_at" datetime field, such as notification_sent_at,
        deleted_at, or cancelled_at, and takes the minimum non-null datetime from these (or
        returns null if they are all null).
        """
        if self.is_active:
            return None
        deactivated_dt = None
        for field in self.is_active_filter().keys():
            if hasattr(self, field + "_at"):
                field_changed_at = getattr(self, field + "_at")
                if deactivated_dt is None or (
                    field_changed_at is not None and field_changed_at < deactivated_dt
                ):
                    deactivated_dt = field_changed_at
        return deactivated_dt

    @staticmethod
    def is_waiting_for_close_filter():
        """
        Returns a tuple of defining the behavior of the is_waiting_for_close property
        (defining whether the registration is waiting to send a close notification to the user
        once the section closes).
        Used for database filtering of registrations (you cannot
        filter by a property value); unpack the filters with a single star
        (NOT a double star like is_active_filter).
        Example:
            Registration.objects.filter(*Registration.is_waiting_for_close_filter())

        As is the case with any Q filters, you must unpack these filters positionally before any
        kwarg filters. If you are unfamiliar with Q queries, see the following docs:
        https://docs.djangoproject.com/en/3.1/topics/db/queries/#complex-lookups-with-q-objects

        All of these conditions are straightforward except for the last. The last condition
        effectively guarantees the next registration in this registration's resubscribe chain
        (if it exists) hasn't been deleted or cancelled. If the user has auto-resubscribe on and
        then cancels the next registration, we don't want the previous registration to send
        a close notification. Based on the way registrations are shown to the user in PCA,
        they would expect cancelling or deleting the head of a resubscribe chain to halt all
        notifications, close or otherwise, from that chain; this condition guarantees that.
        Note that the only way for a registration 2 away from this one would be canceled is if
        an alert was sent for the next registration, meaning a close notification for this
        registration must have already been sent so close_notification_sent=True, or otherwise
        the user cancelled and resubscribed multiple times, which would mean the next registration
        would be cancelled. In all cases, is_waiting_for_close would correctly be False based
        on these filters.
        """
        return (
            Q(notification_sent=True),
            Q(close_notification=True),
            Q(deleted=False),
            Q(cancelled=False),
            Q(close_notification_sent=False),
            (
                Q(resubscribed_to__isnull=True)
                | (
                    Q(resubscribed_to__isnull=False)  # SQL short-circuit logic is not guaranteed
                    & Q(resubscribed_to__cancelled=False)
                    & Q(resubscribed_to__deleted=False)
                )
            ),
        )

    @property
    def is_waiting_for_close(self):
        """
        True if the registration is waiting to send a close notification to the user
        once the section closes.  False otherwise.
        """

        # WARNING: you should be frugal with your usage of this property, since it hits the DB
        # each time it is called.

        return Registration.objects.filter(
            *Registration.is_waiting_for_close_filter(), id=self.id
        ).exists()

    @property
    def last_notification_sent_at(self):
        """
        The last time the user was sent an opening notification for this registration's
        section. This property is None (or null in JSON) if no notification has been sent to the
        user for this registration's section.

        This is used on the frontend to tell the user a last time an alert was sent for
        the SECTION of a certain registration in the manage alerts page. Since the idea of
        Registration objects and resubscribe chains is completely abstracted out of the User's
        understanding, they expect alerts to work by section (so the "LAST NOTIFIED"
        column should tell them the last time they were alerted about that section).
        """
        return (
            self.section.registrations.filter(user=self.user, notification_sent_at__isnull=False)
            .aggregate(max_notification_sent_at=Max("notification_sent_at"))
            .get("max_notification_sent_at", None)
        )

    def __str__(self):
        return "%s: %s @ %s" % (
            (str(self.user) if self.user is not None else None) or self.email or self.phone,
            str(self.section),
            str(self.created_at),
        )

    def validate_phone(self):
        """
        This method converts the phone field to the E164 format, unless the number is in a form
        unparseable by the [phonenumbers library](https://pypi.org/project/phonenumbers/),
        in which case it sets it to None.
        """
        try:
            phone_number = phonenumbers.parse(self.phone, "US")
            self.phone = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.phonenumberutil.NumberParseException:
            # if the phone number is unparseable, don't include it.
            self.phone = None

    def save(self, load_script=False, *args, **kwargs):
        """
        This save method converts the phone field to E164 format, or sets it to
        None if it is unparseable. Then, if the user field is not None, but either of the phone
        or email fields are not None, it moves the info in the phone / email fields
        to the user object (this was only a concern during the PCA refresh transition
        process and is left in for redundancy).
        Then, if original_created_at is None, it sets the original_created_at field to be
        created_at if the registration is the tail of its resubscribe chain, and traverses the
        resubscribe chain to get the original registration's created at otherwise, properly
        setting the original_created_at field. Note that the resubscribe logic carries over
        the original_created_at field to new registrations created by a resubscribe, so the
        case in which the chain is traversed to find the proper value for original_created_at is
        only for redundancy.
        It finally calls the normal save method with args and kwargs.
        Asynchronously after the save completes successfully, if load_script is set to False
        and the registration's semester is the current semester,
        it updates the PcaDemandExtrema models and current_demand_extrema cache to reflect
        the demand change if this registration was just created or deactivated.
        """
        from alert.tasks import registration_update

        update_registration_volume = (
            not load_script
        ) and self.section.semester == get_current_semester()
        if update_registration_volume:
            try:
                was_active = Registration.objects.get(id=self.id).is_active
            except Registration.DoesNotExist:
                was_active = False
        self.validate_phone()
        if self.user is not None:
            if self.email is not None:
                user_data, _ = UserProfile.objects.get_or_create(user=self.user)
                user_data.email = self.email
                user_data.save()
                self.user.profile = user_data
                self.user.save()
                self.email = None
            if self.phone is not None:
                user_data, _ = UserProfile.objects.get_or_create(user=self.user)
                user_data.phone = self.phone
                user_data.save()
                self.user.profile = user_data
                self.user.save()
                self.phone = None
        super().save(*args, **kwargs)
        if self.original_created_at is None:
            if self.resubscribed_from is None:
                self.original_created_at = self.created_at
            else:
                self.original_created_at = self.get_original_registration_rec().created_at
        super().save()
        if update_registration_volume:
            is_now_active = self.is_active
            registration_update.delay(self.section.id, was_active, is_now_active, self.updated_at)

    def alert(self, forced=False, sent_by="", close_notification=False):
        """
        Returns true iff an alert was successfully sent through at least one medium to the user.
        """

        if not forced:
            if close_notification and not self.is_waiting_for_close:
                return False
            if not close_notification and not self.is_active:
                return False

        push_notification = (
            self.user and self.user.profile and self.user.profile.push_notifications
        )  # specifies whether we should use a push notification instead of a text
        text_result = False
        if not push_notification and not close_notification:
            # never send close notifications by text
            text_result = Text(self).send_alert(close_notification=close_notification)
            if text_result is None:
                logging.debug(
                    "ERROR OCCURRED WHILE ATTEMPTING TEXT NOTIFICATION FOR " + self.__str__()
                )
        email_result = Email(self).send_alert(close_notification=close_notification)
        if email_result is None:
            logging.debug(
                "ERROR OCCURRED WHILE ATTEMPTING EMAIL NOTIFICATION FOR " + self.__str__()
            )
        push_notif_result = False
        if push_notification:
            push_notif_result = PushNotification(self).send_alert(
                close_notification=close_notification
            )
            if push_notif_result is None:
                logging.debug(
                    "ERROR OCCURRED WHILE ATTEMPTING PUSH NOTIFICATION FOR " + self.__str__()
                )
        if not email_result and not text_result and not push_notif_result:
            logging.debug("ALERT CALLED BUT NOTIFICATION NOT SENT FOR " + self.__str__())
            return False
        if not close_notification:
            logging.debug("NOTIFICATION SENT FOR " + self.__str__())
            self.notification_sent = True
            self.notification_sent_at = timezone.now()
            self.notification_sent_by = sent_by
            self.save()
            if self.auto_resubscribe:
                self.resubscribe()
            return True
        else:
            logging.debug("CLOSE NOTIFICATION SENT FOR " + self.__str__())
            self.close_notification_sent = True
            self.close_notification_sent_at = timezone.now()
            self.close_notification_sent_by = sent_by
            self.save()
            return True

    def resubscribe(self):
        """
        Resubscribe for notifications. If the head of this registration's resubscribe chain
        is active, just return that registration (don't create a new active registration
        for no reason). Otherwise, add a new active registration as the new head of the
        resubscribe chain.

        Resubscription is idempotent. No matter how many times you call it (without
        alert() being called on the registration), only one Registration model will
        be created.
        :return: Registration object for the resubscription
        """
        most_recent_reg = self.get_most_current_rec()

        if most_recent_reg.is_active:  # if the head of this resub chain is active
            return most_recent_reg  # don't create duplicate registrations for no reason.

        new_registration = Registration(
            user=self.user,
            email=self.email,
            phone=self.phone,
            section=self.section,
            auto_resubscribe=self.auto_resubscribe,
            close_notification=self.close_notification,
            resubscribed_from=most_recent_reg,
            original_created_at=self.original_created_at,
        )
        new_registration.save()
        return new_registration

    def get_resubscribe_group_sql(self):
        """
        This is an optimization that we can use if we need to but as of now it is unused.
        ^ Remove this comment if you use it.
        DO NOT add variable parameters or reference external variables improperly
        (beware of SQL injection attacks)
        https://docs.djangoproject.com/en/3.0/topics/db/sql/
        :return: A QuerySet of all the registrations in this registration's resubscribe chain.
        """
        if not isinstance(self.id, int):
            raise ValueError("ID must be an int")
        return Registration.objects.raw(
            """
            WITH RECURSIVE
            cte_resubscribes_forward AS (
                SELECT
                    *
                FROM
                    alert_registration
                WHERE id=%s
                UNION ALL
                SELECT
                    e.*
                FROM
                    alert_registration e
                    INNER JOIN cte_resubscribes_forward o
                        ON o.id = e.resubscribed_from_id ),
            cte_resubscribes_backward AS (
                SELECT
                    *
                FROM
                    alert_registration
                WHERE id=%s
                UNION ALL
                SELECT
                    e.*
                FROM
                    alert_registration e
                    INNER JOIN cte_resubscribes_backward o
                        ON o.resubscribed_from_id = e.id )
            SELECT
                *
                FROM
                    cte_resubscribes_forward
            UNION
            SELECT
                *
                FROM
                    cte_resubscribes_backward;""",
            (self.id, self.id),  # do not add variables here that could cause vulnerabilities
            # id is an integer (checked above), and therefore cannot be used for SQL injection
        )

    def get_most_current_sql(self):
        """
        This calls get_resubscribe_group_sql, which is an optimization that we can use if we need
        to but as of now it is unused.
        ^ Remove this comment if you use it.
        :return: The head of the resubscribe chain (the most recent registration).
        """
        for r in self.get_resubscribe_group_sql():
            if not hasattr(r, "resubscribed_to"):
                return r
        raise ObjectDoesNotExist(
            "This means an invariant is violated in the database (a resubscribe group should "
            + "always have an element with no resubscribed_to)"
        )

    def get_original_registration_sql(self):
        """
        This calls get_resubscribe_group_sql, which is an optimization that we can use if we need
        to but as of now it is unused.
        ^ Remove this comment if you use it.
        :return: The tail of the resubscribe chain (the original registration).
        """
        for r in self.get_resubscribe_group_sql():
            if r.resubscribed_from is None:
                return r
        raise ObjectDoesNotExist(
            "This means an invariant is violated in the database (a resubscribe group should "
            + "always have an element with no resubscribed_from)"
        )

    def get_most_current_rec(self):
        """
        This method recursively gets the head of the resubscribe chain. It is much less efficient
        than get_most_current_sql, but less prone to opening injection vulnerabilities as a
        result of improper future modifications, so it is currently used. For tasks which require
        higher efficiency, use get_most_current_sql. If you ever switch over to
        using get_most_current_sql, be sure to change all the usages of this method and
        modify the comments under all of these get registration methods.
        :return: The head of the resubscribe chain (the most recent registration).
        """
        if hasattr(self, "resubscribed_to"):
            return self.resubscribed_to.get_most_current_rec()
        else:
            return self

    def get_original_registration_rec(self):
        """
        This method recursively gets the tail of the resubscribe chain. It is much less efficient
        than get_original_registration_sql, but less prone to opening injection vulnerabilities as
        a result of improper future modifications, so it is currently used. For tasks which
        require higher efficiency, use get_original_registration_sql. If you ever switch over to
        using get_original_registration_sql, be sure to change all the usages of this method and
        modify the comments under all of these get registration methods.
        :return: The tail of the resubscribe chain (the original registration).
        """
        if self.resubscribed_from is not None:
            return self.resubscribed_from.get_original_registration_rec()
        else:
            return self


def register_for_course(
    course_code,
    email_address=None,
    phone=None,
    source=SOURCE_PCA,
    api_key=None,
    user=None,
    auto_resub=False,
    close_notification=False,
):
    """
    This method is for the PCA 3rd party API (originally planned to service
    Penn Course Notify, until Notify's rejection of PCA's help and eventual downfall
    (coincidence? we think not...). It still may be used in the future so we are
    keeping the code.
    Returns RegStatus.<STATUS>, section.full_code, registration
    or None for the second two when appropriate
    """
    if (not user and not email_address and not phone) or (
        user
        and not user.profile.email
        and not user.profile.phone
        and not user.profile.push_notifications
    ):
        return RegStatus.NO_CONTACT_INFO, None, None
    try:
        course, section = get_course_and_section(course_code, get_current_semester())
    except Course.DoesNotExist:
        return RegStatus.COURSE_NOT_FOUND, None, None
    except Section.DoesNotExist:
        return RegStatus.COURSE_NOT_FOUND, None, None
    except ValueError:
        return RegStatus.COURSE_NOT_FOUND, None, None

    if user is None:
        registration = Registration(
            section=section, email=email_address, phone=phone, source=source
        )
        registration.validate_phone()
        if section.registrations.filter(
            email=email_address, phone=registration.phone, **Registration.is_active_filter()
        ).exists():
            return RegStatus.OPEN_REG_EXISTS, section.full_code, None
    else:
        if section.registrations.filter(user=user, **Registration.is_active_filter()).exists():
            return RegStatus.OPEN_REG_EXISTS, section.full_code, None
        if close_notification and not user.profile.email and not user.profile.push_notifications:
            return RegStatus.TEXT_CLOSE_NOTIFICATION, section.full_code, None
        registration = Registration(section=section, user=user, source=source)
        registration.auto_resubscribe = auto_resub
        registration.close_notification = close_notification

    registration.api_key = api_key
    registration.save()

    return RegStatus.SUCCESS, section.full_code, registration


class PcaDemandExtrema(models.Model):
    """
    This model tracks changes in the extrema (i.e. highest and lowest values) of
    raw PCA demand ratios across all sections in a given semester.
    Raw PCA demand (as opposed to "Relative PCA demand",
    which maps demand values between extrema to a fixed range of [0,4]) is defined
    for any given section as (PCA registration volume)/(section capacity).
    Note that capacity is not stored as a field, while volume is. We do not track capacity changes,
    and for this reason, the recompute_demand_extrema function (in the recomputestats
    management command script) should be run after each run of the registrarimport script,
    in case capacity changes affect historical extrema.
    """

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="The datetime at which the extrema were updated.",
    )

    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The semester of this demand extrema (of the form YYYYx where x is
        A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.
        """
        ),
    )

    most_popular_section = models.ForeignKey(
        Section,
        related_name="most_popular_extrema_occurences",
        on_delete=models.CASCADE,
        help_text="A most popular section.",
    )

    most_popular_volume = models.IntegerField(
        help_text="The registration volume of the most popular section at this time."
    )

    least_popular_section = models.ForeignKey(
        Section,
        related_name="least_popular_extrema_occurences",
        on_delete=models.CASCADE,
        help_text="A least popular section.",
    )

    least_popular_volume = models.IntegerField(
        help_text="The registration volume of the least popular section at this time."
    )

    percent_through_add_drop_period = models.FloatField(
        default=0,
        help_text="The percentage through the add/drop period at which this demand extrema change "
        "occurred. This percentage is constrained within the range [0,1].",
    )  # This field is maintained in the save() method of alerts.models.AddDropPeriod,
    # and the save() method of PcaDemandExtrema

    in_add_drop_period = models.BooleanField(
        default=False, help_text="Was this demand extrema created during the add/drop period?"
    )  # This field is maintained in the save() method of alerts.models.AddDropPeriod,
    # and the save() method of PcaDemandExtrema

    def __str__(self):
        return f"PcaDemandExtrema {self.semester} @ {self.created_at}"

    @property
    def highest_raw_demand(self):
        if self.most_popular_section.capacity is None or self.most_popular_section.capacity <= 0:
            return None
        return float(self.most_popular_volume) / float(self.most_popular_section.capacity)

    @property
    def lowest_raw_demand(self):
        if self.least_popular_section.capacity is None or self.least_popular_section.capacity <= 0:
            return None
        return float(self.least_popular_volume) / float(self.least_popular_section.capacity)

    @staticmethod
    def get_current_demand_extrema(semester):
        """
        Returns the latest PcaDemandExtrema object for the specified semester,
        or None if no valid extrema exist for the specified semester (this won't be the case as
        long as at least 1 section for the given semester has a non-null and positive capacity).
        Semester defaults to the current semester.

        See the above model docstring for an explanation of PCA demand.
        """
        current_sem = get_current_semester()
        if semester is None:
            semester = current_sem
        is_current_sem = semester == current_sem
        cache_context = (
            cache.lock("current_demand_extrema")
            if (is_current_sem and hasattr(cache, "lock"))
            else nullcontext()
        )
        with transaction.atomic(), cache_context:
            sentinel = object()
            current_demand_extrema = sentinel
            if is_current_sem:
                current_demand_extrema = cache.get("current_demand_extrema", sentinel)
            if current_demand_extrema == sentinel or current_demand_extrema["semester"] != semester:
                try:
                    latest_extrema_ob = (
                        PcaDemandExtrema.objects.filter(semester=semester)
                        .select_for_update()
                        .latest("created_at")
                    )
                    current_demand_extrema = latest_extrema_ob
                except PcaDemandExtrema.DoesNotExist:
                    current_demand_extrema = None
                if is_current_sem:
                    cache.set("current_demand_extrema", current_demand_extrema, timeout=None)
        return current_demand_extrema

    def save(self, *args, **kwargs):
        if "add_drop_period" in kwargs:
            add_drop_period = kwargs["add_drop_period"]
            del kwargs["add_drop_period"]
        else:
            add_drop_period = AddDropPeriod.objects.get(semester=self.semester)
        super().save(*args, **kwargs)
        created_at = self.created_at
        start = add_drop_period.estimated_start
        end = add_drop_period.estimated_end
        if created_at < start:
            self.in_add_drop_period = False
            self.percent_through_add_drop_period = 0
        elif created_at > end:
            self.in_add_drop_period = False
            self.percent_through_add_drop_period = 1
        else:
            self.in_add_drop_period = True
            self.percent_through_add_drop_period = (created_at - start) / (end - start)
        super().save()


def validate_add_drop_semester(semester):
    """
    Validate the passed-in string as a fall or spring semester, such as 2020A or 2021C.
    """
    if len(semester) != 5:
        raise ValidationError(
            f"Semester {semester} is invalid; valid semesters contain 5 characters."
        )
    if semester[4] not in ["A", "C"]:
        raise ValidationError(f"Semester {semester} is invalid; valid semesters end in 'A' or 'C'.")
    if not semester[:4].isnumeric():
        raise ValidationError(
            f"Semester {semester} is invalid; the 4-letter prefix of a valid semester is numeric."
        )


class AddDropPeriod(models.Model):
    """
    This model tracks the start and end date of the add drop period corresponding to
    a semester (only fall or spring semesters are supported).
    """

    semester = models.CharField(
        max_length=5,
        db_index=True,
        unique=True,
        validators=[validate_add_drop_semester],
        help_text=dedent(
            """
        The semester of this add drop period (of the form YYYYx where x is
        A [for spring], or C [fall]), e.g. `2019C` for fall 2019.
        """
        ),
    )
    start = models.DateTimeField(
        null=True, blank=True, help_text="The datetime at which the add drop period started."
    )
    end = models.DateTimeField(
        null=True, blank=True, help_text="The datetime at which the add drop period ended."
    )

    # estimated_start and estimated_end are filled in automatically in the overridden save method,
    # so there is no need to maintain them (they are derivative fields of start and end).
    # The only reason why they aren't properties is we sometimes need to use them in database
    # filters / aggregations.
    estimated_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text=dedent(
            """
            This field estimates the start of the add/drop period based on the semester
            and historical data, even if the start field hasn't been filled in yet.
            It equals the start of the add/drop period for this semester if it is explicitly set,
            otherwise the most recent non-null start to an add/drop period, otherwise
            (if none exist), estimate as April 5 @ 7:00am ET of the same year (for a fall semester),
            or November 16 @ 7:00am ET of the previous year (for a spring semester).
            """
        ),
    )
    estimated_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text=dedent(
            """
            This field estimates the end of the add/drop period based on the semester
            and historical data, even if the end field hasn't been filled in yet.
            The end of the add/drop period for this semester, if it is explicitly set, otherwise
        the most recent non-null end to an add/drop period, otherwise (if none exist),
        estimate as October 12 @ 11:59pm ET (for a fall semester),
        or February 22 @ 11:59pm ET (for a spring semester),
        of the same year.
            """
        ),
    )

    def get_percent_through_add_drop(self, dt):
        """
        The percentage through this add/drop period at which this dt occured.
        This percentage is constrained within the range [0,1]."
        """
        start = self.estimated_start
        end = self.estimated_end
        if dt < start:
            return 0
        if dt > end:
            return 1
        else:
            return float((dt - start) / (end - start))

    def save(self, *args, **kwargs):
        self.estimated_start = self.estimate_start()
        self.estimated_end = self.estimate_end()
        period = self.estimated_end - self.estimated_start
        for model, sem_filter_key in [
            (StatusUpdate, "section__course__semester"),
            (PcaDemandExtrema, "semester"),
        ]:
            sem_filter = {sem_filter_key: self.semester}
            model.objects.filter(**sem_filter).update(
                in_add_drop_period=Case(
                    When(
                        Q(created_at__gte=self.estimated_start)
                        & Q(created_at__lte=self.estimated_end),
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=models.BooleanField(),
                ),
                percent_through_add_drop_period=Case(
                    When(Q(created_at__lte=self.estimated_start), then=Value(0),),
                    When(Q(created_at__gte=self.estimated_end), then=Value(1)),
                    default=(F("created_at") - Value(self.estimated_start)) / Value(period),
                    output_field=models.FloatField(),
                ),
            )
        super().save(*args, **kwargs)

    def estimate_start(self):
        """
        The start of the add/drop period for this semester, if it is explicitly set, otherwise
        the most recent non-null start to an add/drop period, otherwise (if none exist),
        estimate as April 5 @ 7:00am ET of the same year (for a fall semester),
        or November 16 @ 7:00am ET of the previous year (for a spring semester).
        """
        if self.start is None:
            last_start = (
                AddDropPeriod.objects.filter(
                    start__isnull=False, semester__endswith=str(self.semester)[4]
                )
                .order_by("-semester")
                .first()
            )
            if str(self.semester)[4] == "C":  # fall semester
                s_year = int(str(self.semester)[:4])
                s_month = 4
                s_day = 5
            else:  # spring semester
                s_year = int(str(self.semester)[:4]) - 1
                s_month = 11
                s_day = 16
            if last_start is None:
                tz = pytz.timezone(TIME_ZONE)
                return make_aware(
                    datetime.strptime(f"{s_year}-{s_month}-{s_day} 07:00", "%Y-%m-%d %H:%M"),
                    timezone=tz,
                )
            return last_start.start.replace(year=s_year)
        return self.start

    def estimate_end(self):
        """
        The end of the add/drop period for this semester, if it is explicitly set, otherwise
        the most recent non-null end to an add/drop period, otherwise (if none exist),
        estimate as October 12 @ 11:59pm ET (for a fall semester),
        or February 22 @ 11:59pm ET (for a spring semester),
        of the same year.
        """
        if self.end is None:
            last_end = (
                AddDropPeriod.objects.filter(
                    end__isnull=False, semester__endswith=str(self.semester)[4]
                )
                .order_by("-semester")
                .first()
            )
            e_year = int(str(self.semester)[:4])
            if last_end is None:
                if str(self.semester)[4] == "C":  # fall semester
                    e_month = 10
                    e_day = 12
                else:  # spring semester
                    e_month = 2
                    e_day = 22
                tz = pytz.timezone(TIME_ZONE)
                return make_aware(
                    datetime.strptime(f"{e_year}-{e_month}-{e_day} 23:59", "%Y-%m-%d %H:%M"),
                    timezone=tz,
                )
            return last_end.end.replace(year=e_year)
        return self.end

    def __str__(self):
        return f"AddDropPeriod {self.semester}"
