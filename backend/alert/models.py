import logging
from enum import Enum, auto

import phonenumbers  # library for parsing and formatting phone numbers.
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from alert.alerts import Email, PushNotification, Text
from courses.models import Course, Section, UserProfile, get_current_semester
from courses.util import get_course_and_section


class RegStatus(Enum):
    SUCCESS = auto()
    OPEN_REG_EXISTS = auto()
    COURSE_OPEN = auto()
    COURSE_NOT_FOUND = auto()
    NO_CONTACT_INFO = auto()


SOURCE_PCA = "PCA"
SOURCE_API = "API"


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    original_created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

    SOURCE_CHOICES = (
        ("PCA", "Penn Course Alert"),
        ("API", "3rd Party Integration"),
        ("PCP", "Penn Course Plan"),
        ("PCR", "Penn Course Review"),
        ("PM", "Penn Mobile"),
    )

    # Where did the registration come from?
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    api_key = models.ForeignKey("courses.APIKey", blank=True, null=True, on_delete=models.CASCADE)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    # going forward, email and phone will be None
    # and contact information can be found in the user's UserData object
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=100)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # has the user enabled mobile notifications
    push_notifications = models.BooleanField(default=False)
    # changed to True if user cancels notification
    cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    # changed to True if user deletes notification,
    # never changed back (a new model is created on resubscription)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    # does the user have auto-mute enabled for this alert?
    auto_resubscribe = models.BooleanField(default=False)
    # changed to True once notification is sent out for this registration
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    # has the user opted-in to receive notifications when the course opens and then closes.
    close_notification = models.BooleanField(default=False)
    # changed to True if close notification is sent out
    close_notification_sent = models.BooleanField(default=False)
    close_notification_sent_at = models.DateTimeField(blank=True, null=True)

    METHOD_CHOICES = (
        ("", "Unsent"),
        ("LEG", "[Legacy] Sequence of course API requests"),
        ("WEB", "Webhook"),
        ("SERV", "Course Status Service"),
        ("ADM", "Admin Interface"),
    )
    notification_sent_by = models.CharField(
        max_length=16, choices=METHOD_CHOICES, default="", blank=True
    )
    close_notification_sent_by = models.CharField(
        max_length=16, choices=METHOD_CHOICES, default="", blank=True
    )

    # track resubscriptions
    resubscribed_from = models.OneToOneField(
        "Registration",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="resubscribed_to",
    )

    def __str__(self):
        return "%s: %s" % (
            (self.user.__str__() if self.user is not None else None) or self.email or self.phone,
            self.section.__str__(),
        )

    def validate_phone(self):
        """
        Store phone numbers in the format recommended by Twilio.
        """
        try:
            phone_number = phonenumbers.parse(self.phone, "US")
            self.phone = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.phonenumberutil.NumberParseException:
            # if the phone number is unparseable, don't include it.
            self.phone = None

    def save(self, *args, **kwargs):
        self.validate_phone()
        if self.user is not None:
            if self.email is not None:
                user_data, _ = UserProfile.objects.get_or_create(user=self.user)
                user_data.email = self.email
                user_data.save()
                self.email = None
            if self.phone is not None:
                user_data, _ = UserProfile.objects.get_or_create(user=self.user)
                user_data.phone = self.phone
                user_data.save()
                self.phone = None
        super().save(*args, **kwargs)
        if self.original_created_at is None:
            if self.resubscribed_from is None:
                self.original_created_at = self.created_at
            else:
                self.original_created_at = self.get_original_registration_rec().created_at
        super().save()

    @staticmethod
    def is_active_filter():
        """
        Returns a dict of filters defining the behavior of the is_active property.
        Also used in database filtering of registrations (you cannot filter by a property value).
        """
        return {"notification_sent": False, "deleted": False, "cancelled": False}

    @property
    def is_active(self):
        """
        Returns True iff the registration would send a notification
        when the watched section changes to open
        """
        for k, v in self.is_active_filter().items():
            if getattr(self, k) != v:
                return False
        return True

    @staticmethod
    def is_waiting_for_close_filter():
        """
        Returns a dict of filters defining the behavior of the is_waiting_for_close property.
        Also used in database filtering of registrations (you cannot filter by a property value).
        """
        return {
            "notification_sent": True,
            "close_notification": True,
            "deleted": False,
            "cancelled": False,
            "close_notification_sent": False,
        }

    @property
    def is_waiting_for_close(self):
        """
        Returns True iff the registration would send a close notification
        when the watched section changes to closed
        """
        for k, v in self.is_waiting_for_close_filter().items():
            if getattr(self, k) != v:
                return False
        return True

    def alert(self, forced=False, sent_by="", close_notification=False):
        if forced or self.is_active:
            text_result = Text(self).send_alert()
            email_result = Email(self).send_alert()
            push_notif_result = PushNotification(self).send_alert()
            if not close_notification:
                logging.debug("NOTIFICATION SENT FOR " + self.__str__())
                self.notification_sent = True
                self.notification_sent_at = timezone.now()
                self.notification_sent_by = sent_by
                self.save()
                if self.auto_resubscribe:
                    self.resubscribe()
            else:
                logging.debug("CLOSE NOTIFICATION SENT FOR " + self.__str__())
                self.close_notification_sent = True
                self.close_notification_sent_at = timezone.now()
                self.close_notification_sent_by = sent_by
                self.save()
            return (
                email_result is not None
                and text_result is not None
                and push_notif_result is not None
            )  # True if no error in email/text/push-notification.
        else:
            return False

    def resubscribe(self):
        """
        Resubscribe for notifications. If the registration this is called on
        has had its notification sent, a new registration is made. If it hasn't,
        return the most recent registration in the resubscription chain which hasn't
        been used yet.

        Resubscription is idempotent. No matter how many times you call it (without
        alert() being called on the registration), only one Registration model will
        be created.
        :return: Registration object for the resubscription
        """
        most_recent_reg = self.get_most_current_rec()

        if (
            not most_recent_reg.notification_sent and not most_recent_reg.cancelled
        ):  # if a notification hasn't been sent on this recent one (and it hasn't been cancelled),
            return most_recent_reg  # don't create duplicate registrations for no reason.

        new_registration = Registration(
            user=self.user,
            email=self.email,
            phone=self.phone,
            section=self.section,
            auto_resubscribe=self.auto_resubscribe,
            close_notification=self.close_notification,
            push_notifications=self.push_notifications,
            resubscribed_from=most_recent_reg,
            original_created_at=self.original_created_at,
        )
        new_registration.save()
        return new_registration

    def get_resubscribe_group_sql(self):
        # This is an optimization that we can use if we need to but as of now it is unused.
        # ^ Remove this comment if you use it.
        # DO NOT add variable parameters or reference external variables improperly
        # (beware of SQL injection attacks)
        # https://docs.djangoproject.com/en/3.0/topics/db/sql/
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
            (self.id, self.id),
        )

    def get_most_current_sql(self):
        for r in self.get_resubscribe_group_sql():
            if not hasattr(r, "resubscribed_to"):
                return r
        raise ObjectDoesNotExist(
            "This means an invariant is violated in the database (a resubscribe group should "
            + "always have an element with no resubscribed_to)"
        )

    def get_original_registration_sql(self):
        for r in self.get_resubscribe_group_sql():
            if r.resubscribed_from is None:
                return r
        raise ObjectDoesNotExist(
            "This means an invariant is violated in the database (a resubscribe group should "
            + "always have an element with no resubscribed_from)"
        )

    def get_most_current_rec(self):
        if hasattr(self, "resubscribed_to"):
            return self.resubscribed_to.get_most_current_rec()
        else:
            return self

    def get_original_registration_rec(self):
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
    push_notifications=False,
):
    if not email_address and not phone and not user:
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
        if Registration.objects.filter(
            section=section,
            email=email_address,
            phone=registration.phone,
            **Registration.is_active_filter()
        ).exists():
            return RegStatus.OPEN_REG_EXISTS, section.full_code, None
    else:
        if Registration.objects.filter(
            section=section, user=user, **Registration.is_active_filter()
        ).exists():
            return RegStatus.OPEN_REG_EXISTS, section.full_code, None
        registration = Registration(section=section, user=user, source=source)
        registration.auto_resubscribe = auto_resub
        registration.close_notification = close_notification
        registration.push_notifications = push_notifications

    registration.api_key = api_key
    registration.save()
    return RegStatus.SUCCESS, section.full_code, registration
