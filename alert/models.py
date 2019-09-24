import logging
from enum import Enum, auto

import phonenumbers  # library for parsing and formatting phone numbers.
from django import urls
from django.conf import settings
from django.db import models
from django.utils import timezone
from shortener.models import Url

from alert.alerts import Email, Text
from courses.models import Section, get_current_semester
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

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=100)
    # section that the user registered to be notified about
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
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
        super().save(*args, **kwargs)

    @property
    def resub_url(self):
        """Get the resubscribe URL associated with this registration"""
        full_url = '%s%s' % (settings.PCA_URL, urls.reverse('resubscribe',
                                                            kwargs={'id_': self.id},
                                                            urlconf='alert.urls'))
        return Url.objects.get_or_create(full_url).shortened

    def alert(self, forced=False, sent_by=''):
        if forced or not self.notification_sent:
            text_result = Text(self).send_alert()
            email_result = Email(self).send_alert()
            logging.debug('NOTIFICATION SENT FOR ' + self.__str__())
            self.notification_sent = True
            self.notification_sent_at = timezone.now()
            self.notification_sent_by = sent_by
            self.save()
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
        return RegStatus.NO_CONTACT_INFO
    course, section = get_course_and_section(course_code, get_current_semester())
    registration = Registration(section=section, email=email_address, phone=phone, source=source)
    registration.validate_phone()

    if Registration.objects.filter(section=section,
                                   email=email_address,
                                   phone=registration.phone,
                                   notification_sent=False).exists():
        return RegStatus.OPEN_REG_EXISTS

    registration.api_key = api_key
    registration.save()
    return RegStatus.SUCCESS


class CourseUpdate(models.Model):
    STATUS_CHOICES = (
        ('O', 'Open'),
        ('C', 'Closed'),
        ('X', 'Cancelled'),
        ('', 'Unlisted')
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    alert_sent = models.BooleanField()
    request_body = models.TextField()

    def __str__(self):
        d = dict(self.STATUS_CHOICES)
        return f'{self.section.__str__()} - {d[self.old_status]} to {d[self.new_status]}'


def record_update(section_id, semester, old_status, new_status, alerted, req):
    try:
        _, section = get_course_and_section(section_id, semester)
    except ValueError:
        return None
    u = CourseUpdate(section=section,
                     old_status=old_status,
                     new_status=new_status,
                     alert_sent=alerted,
                     request_body=req)
    u.save()
    return u


def update_course_from_record(update):
    if update is not None:
        section = update.section
        section.status = update.new_status
        section.save()
