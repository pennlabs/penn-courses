import logging
from enum import Enum, auto

import phonenumbers  # library for parsing and formatting phone numbers.
from django import urls
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from shortener.models import Url

from alert.alerts import Email, Text
from courses.models import Course, Section, UserProfile, get_current_semester
from courses.util import get_course_and_section


class RegStatus(Enum):
    SUCCESS = auto()
    OPEN_REG_EXISTS = auto()
    COURSE_OPEN = auto()
    COURSE_NOT_FOUND = auto()
    NO_CONTACT_INFO = auto()


SOURCE_PCA = 'PCA'
SOURCE_API = 'API'


class Registration(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    SOURCE_CHOICES = (
        ('PCA', 'Penn Course Alert'),
        ('API', '3rd Party Integration'),
        ('PCP', 'Penn Course Plan'),
        ('PCR', 'Penn Course Review'),
        ('PM', 'Penn Mobile')
    )

    # Where did the registration come from?
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    api_key = models.ForeignKey('courses.APIKey', blank=True, null=True, on_delete=models.CASCADE)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    # going forward, email and phone will be None and contact information can be found in the user's UserData object
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=100)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # changed to True if user deletes notification
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    # changed to True if user mutes notification
    muted = models.BooleanField(default=False)
    muted_at = models.DateTimeField(blank=True, null=True)
    # does the user have auto-mute enabled for this alert?
    auto_mute = models.BooleanField(default=True)
    # change to True once notification email has been sent out
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    METHOD_CHOICES = (
        ('', 'Unsent'),
        ('LEG', '[Legacy] Sequence of course API requests'),
        ('WEB', 'Webhook'),
        ('SERV', 'Course Status Service'),
        ('ADM', 'Admin Interface'),
    )
    notification_sent_by = models.CharField(max_length=16, choices=METHOD_CHOICES, default='', blank=True)

    # track resubscriptions
    resubscribed_from = models.OneToOneField('Registration',
                                             blank=True,
                                             null=True,
                                             on_delete=models.SET_NULL,
                                             related_name='resubscribed_to')

    def __str__(self):
        return '%s: %s' % (self.email or self.phone, self.section.__str__())

    def validate_phone(self):
        """Store phone numbers in the format recommended by Twilio."""
        try:
            phone_number = phonenumbers.parse(self.phone, 'US')
            self.phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
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

    @property
    def is_active(self):
        """Returns True iff the registration would send a notification when the watched section changes to open"""
        return not (self.notification_sent or self.muted or self.deleted)

    @property
    def resub_url(self):
        """Get the resubscribe URL associated with this registration"""
        full_url = '%s%s' % (settings.PCA_URL, urls.reverse('resubscribe',
                                                            kwargs={'id_': self.id},
                                                            urlconf='alert.urls'))
        url, _ = Url.objects.get_or_create(full_url)
        return '{}/s/{}'.format(settings.PCA_URL, url.short_id)

    def alert(self, forced=False, sent_by=''):
        if forced or self.is_active:
            text_result = Text(self).send_alert()
            email_result = Email(self).send_alert()
            logging.debug('NOTIFICATION SENT FOR ' + self.__str__())
            self.notification_sent = True
            self.notification_sent_at = timezone.now()
            self.notification_sent_by = sent_by
            self.save()
            if self.auto_mute:
                self.muted = True
            else:
                self.resubscribe()
            return email_result is not None and text_result is not None  # True if no error in email/text.
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
        most_recent_reg = self
        while hasattr(most_recent_reg, 'resubscribed_to'):  # follow the chain of resubscriptions to the most recent one
            most_recent_reg = most_recent_reg.resubscribed_to

        if not most_recent_reg.notification_sent:  # if a notification hasn't been sent on this recent one,
            return most_recent_reg  # don't create duplicate registrations for no reason.

        new_registration = Registration(email=self.email,
                                        phone=self.phone,
                                        section=self.section,
                                        resubscribed_from=most_recent_reg)
        new_registration.save()
        return new_registration


def register_for_course(course_code, email_address, phone, source=SOURCE_PCA, api_key=None):
    if not email_address and not phone:
        return RegStatus.NO_CONTACT_INFO, None
    try:
        course, section = get_course_and_section(course_code, get_current_semester())
    except Course.DoesNotExist:
        return RegStatus.COURSE_NOT_FOUND, None
    except Section.DoesNotExist:
        return RegStatus.COURSE_NOT_FOUND, None
    except ValueError:
        return RegStatus.COURSE_NOT_FOUND, None

    registration = Registration(section=section, email=email_address, phone=phone, source=source)
    registration.validate_phone()

    if Registration.objects.filter(section=section,
                                   email=email_address,
                                   phone=registration.phone,
                                   notification_sent=False).exists():
        return RegStatus.OPEN_REG_EXISTS, section.full_code

    registration.api_key = api_key
    registration.save()
    return RegStatus.SUCCESS, section.full_code
