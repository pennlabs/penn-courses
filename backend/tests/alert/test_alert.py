import base64
import importlib
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from dateutil.tz.tz import gettz
from ddt import data, ddt, unpack
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.signals import post_save
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from options.models import Option
from rest_framework.test import APIClient

from alert import tasks
from alert.alerts import get_meeting_string
from alert.models import SOURCE_PCA, AddDropPeriod, Registration, RegStatus, register_for_course
from alert.tasks import get_registrations_for_alerts
from courses.models import StatusUpdate
from courses.util import (
    get_add_drop_period,
    get_or_create_course_and_section,
    invalidate_current_semester_cache,
    translate_semester,
)
from PennCourses.celery import app as celeryapp
from PennCourses.settings.base import TIME_ZONE
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2019A"

celeryapp.conf.update(CELERY_ALWAYS_EAGER=True)  # run asynchronous tasks synchronously


def contains_all(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


def override_delay(modules_names, before_func, before_kwargs):
    """
    A function that makes delay()ed functions synchronous for testing.  Please read the full docs
    (RTFM) before using to prevent unintended behavior or errors.
    See AlertRegistrationTestCase.simulate_alert for an example of how to use this function

    :param modules_names: a list of 2-tuples of the form (module, name) where module is the module
        in which the delay()ed function is located and name is its name.  Note that each 2-tuple
        corresponds to exactly one delay()ed function.
        Make sure to order the delayed functions' 2-tuples in the
        modules_names list in the order that they will be executed.
        Also, note that each delay()ed function after the first must be
        triggered by the previous one (directly or indirectly).  Otherwise you could just
        call this function multiple times.  If this condition is not met,
        an error will be thrown.  For more complicated use-cases (like patching functions
        between delay()ed functions), you will have to implement the functionality of this
        function yourself, in a custom way tailored to your use-case.
        Example of valid modules_names argument (from AlertRegistrationTestCase.simulate_alert):
            [('alert.tasks', 'send_course_alerts'), ('alert.tasks', 'send_alert')]
    :param before_func: a function (not its name, the actual function as a variable) which will be
        executed to trigger the first delay()ed function in modules_names.
        Note that this function MUST trigger the first delay()ed function in modules_names
        or an error will be thrown.
        Example of a valid before_func argument (from AlertRegistrationTestCase.simulate_alert):
            a function simulating the webhook firing which causes send_course_alerts.delay()
            to be called
    :param before_kwargs: a dictionary of keyword-value arguments which will be
        unpacked and passed into before_func
    """
    if len(modules_names) > 0:
        mn = modules_names[-1]
        with patch(mn[0] + "." + mn[1] + ".delay") as mock_func:
            mock_func.side_effect = getattr(importlib.import_module(mn[0]), mn[1])
            if len(modules_names) == 1:
                before_func(**before_kwargs)
            else:
                override_delay(modules_names[:-1], before_func, before_kwargs)


class RegistrationSaveAutoHeadRegistrationTest(TestCase):
    def setUp(self):
        set_semester()
        user = User.objects.create_user(username="jacob", password="top_secret")
        user.save()
        self.user = user

    def create_reg(self, full_code, **kwargs):
        _, section, _, _ = get_or_create_course_and_section(full_code, TEST_SEMESTER)
        reg = Registration(section=section, user=self.user, **kwargs)
        reg.save()
        return reg

    def test_new(self):
        a = self.create_reg("CIS-120-001")
        self.assertEqual(a.head_registration, a)

    def test_delete_max_id(self):
        self.create_reg("CIS-120-001")
        self.create_reg("CIS-160-001")
        c = self.create_reg("CIS-121-001")
        c.delete()
        d = self.create_reg("CIS-240-001")
        self.assertEqual(d.head_registration, d)

    def test_delete_min_id(self):
        a = self.create_reg("CIS-120-001")
        self.create_reg("CIS-160-001")
        self.create_reg("CIS-121-001")
        a.delete()
        d = self.create_reg("CIS-240-001")
        self.assertEqual(d.head_registration, d)

    def test_delete_all(self):
        a = self.create_reg("CIS-120-001")
        b = self.create_reg("CIS-160-001")
        c = self.create_reg("CIS-121-001")
        a.delete()
        b.delete()
        c.delete()
        d = self.create_reg("CIS-240-001")
        self.assertEqual(d.head_registration, d)

    def test_update_resub_group(self):
        self.create_reg("CIS-120-001")
        b = self.create_reg("CIS-121-001")
        c = self.create_reg("CIS-121-001", resubscribed_from=b)
        d = self.create_reg("CIS-121-001", resubscribed_from=c)
        b_db = Registration.objects.get(id=b.id)
        c_db = Registration.objects.get(id=c.id)
        d_db = Registration.objects.get(id=d.id)
        self.assertEqual(d.head_registration, d)
        self.assertEqual(b_db.head_registration, d_db)
        self.assertEqual(c_db.head_registration, d_db)
        self.assertEqual(d_db.head_registration, d_db)


@patch("alert.models.PushNotification.send_alert")
@patch("alert.models.Text.send_alert")
@patch("alert.models.Email.send_alert")
class SendAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, section, _, _ = get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)
        section.capacity = 30
        section.save()
        self.r_legacy = Registration(email="yo@example.com", phone="+15555555555", section=section)
        self.r_legacy.save()
        user = User.objects.create_user(username="jacob", password="top_secret")
        user.save()
        self.r = Registration(
            email="yo@example.com", phone="+15555555555", section=section, user=user
        )
        self.r.save()

    def test_send_alert_legacy(self, mock_email, mock_text, mock_push_notification):
        r_legacy = Registration.objects.get(id=self.r_legacy.id)
        self.assertIsNone(r_legacy.user)
        self.assertEquals("yo@example.com", r_legacy.email)
        self.assertEquals("+15555555555", r_legacy.phone)
        self.assertEquals("CIS-1600-001", r_legacy.section.full_code)
        self.assertFalse(r_legacy.notification_sent)
        self.assertTrue(r_legacy.is_active)
        tasks.send_alert(self.r_legacy.id, False, sent_by="ADM")
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)
        self.assertFalse(mock_push_notification.called)
        r_legacy = Registration.objects.get(id=self.r_legacy.id)
        self.assertTrue(r_legacy.notification_sent)
        self.assertEqual("ADM", r_legacy.notification_sent_by)

    def send_alert_helper(self, mock_email, mock_text, mock_push_notification, push_notification):
        """
        This function checks that tasks.send_alert triggers the proper Alert subclass
        send_alert methods in two cases.  The first case is when push notifications are enabled
        on the underlying registration, and the second case is when they are not.
        """
        self.r.user.profile.push_notifications = push_notification
        self.r.user.profile.save()
        r = Registration.objects.get(id=self.r.id)
        self.assertIsNotNone(r.user)
        self.assertIsNotNone(r.user.profile)
        self.assertEquals("yo@example.com", r.user.profile.email)
        self.assertEquals("+15555555555", r.user.profile.phone)
        self.assertEquals("CIS-1600-001", r.section.full_code)
        self.assertIsNone(r.email)
        self.assertIsNone(r.phone)
        self.assertEquals(push_notification, r.user.profile.push_notifications)
        self.assertFalse(r.notification_sent)
        self.assertTrue(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        self.assertEquals(
            0,
            len(get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="X")),
        )
        self.assertEquals(
            0,
            len(get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="")),
        )
        tasks.send_alert(self.r.id, False, sent_by="ADM")
        r = Registration.objects.get(id=self.r.id)
        self.assertTrue(mock_email.called)
        self.assertEquals(not push_notification, mock_text.called)
        self.assertEquals(push_notification, mock_push_notification.called)
        self.assertTrue(r.notification_sent)
        self.assertIsNotNone("ADM", r.notification_sent_by)
        self.assertEqual("ADM", r.notification_sent_by)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )

    def test_send_alert_push(self, mock_email, mock_text, mock_push_notification):
        self.send_alert_helper(
            mock_email, mock_text, mock_push_notification, push_notification=True
        )

    def test_send_alert(self, mock_email, mock_text, mock_push_notification):
        self.send_alert_helper(
            mock_email, mock_text, mock_push_notification, push_notification=False
        )

    def send_close_notification_helper(
        self,
        mock_email,
        mock_text,
        mock_push_notification,
        push_notification,
        auto_resubscribe,
        manual_resubscribe,
    ):
        """
        This function checks that a call to tasks.send_alert for a close notification triggers
        the proper Alert subclass send_alert methods in 6 cases.  Either push notifications
        are enabled or disabled (push_notification is True or False), auto resubscribe is
        enabled or disabled on the underlying registration (auto_resubscribe is True or False),
        and a manual resubscribe is either triggered or not triggered in the case that
        auto_resubscribe is False (manual_resubscribe is True of False).
        """
        self.r.user.profile.push_notifications = push_notification
        self.r.user.profile.save()
        if not manual_resubscribe:
            self.r.auto_resubscribe = auto_resubscribe
        self.r.close_notification = True
        self.r.notification_sent = True
        self.r.notification_sent_by = "ADM"
        self.r.notification_sent_at = timezone.now()
        self.r.save()
        r = Registration.objects.get(id=self.r.id)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertTrue(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        tasks.send_alert(self.r.id, close_notification=True, sent_by="ADM")
        if manual_resubscribe:
            r.resubscribe()
        r = Registration.objects.get(id=self.r.id)
        self.assertTrue(mock_email.called)
        self.assertFalse(mock_text.called)
        self.assertEquals(push_notification, mock_push_notification.called)
        self.assertTrue(r.notification_sent)
        self.assertIsNotNone(r.notification_sent_at)
        self.assertEqual("ADM", r.notification_sent_by)
        self.assertTrue(r.close_notification_sent)
        self.assertIsNotNone(r.close_notification_sent_at)
        self.assertEqual("ADM", r.close_notification_sent_by)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )

    def test_send_close_notification_push(self, mock_email, mock_text, mock_push_notification):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=True,
            auto_resubscribe=True,
            manual_resubscribe=False,
        )

    def test_send_close_notification_push_autoresub(
        self, mock_email, mock_text, mock_push_notification
    ):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=True,
            auto_resubscribe=False,
            manual_resubscribe=False,
        )

    def test_send_close_notification_autoresub(self, mock_email, mock_text, mock_push_notification):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=False,
            auto_resubscribe=True,
            manual_resubscribe=False,
        )

    def test_send_close_notification(self, mock_email, mock_text, mock_push_notification):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=False,
            auto_resubscribe=False,
            manual_resubscribe=False,
        )

    def test_send_close_notification_push_resub(
        self, mock_email, mock_text, mock_push_notification
    ):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=True,
            auto_resubscribe=False,
            manual_resubscribe=True,
        )

    def test_send_close_notification_resub(self, mock_email, mock_text, mock_push_notification):
        self.send_close_notification_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=False,
            auto_resubscribe=False,
            manual_resubscribe=True,
        )

    def dont_resend_alert_helper(
        self, mock_email, mock_text, mock_push_notification, close_notification
    ):
        """
        This helper checks that tasks.send_alert does not send new alerts for a registration that
        has already triggered an alert in 2 possible cases.  Either it is a regular
        open notification or it is a close notification (close_notification is True or False).
        """
        self.r.notification_sent = True
        self.r.close_notification_sent = True
        self.r.save()
        r = Registration.objects.get(id=self.r.id)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        tasks.send_alert(self.r.id, close_notification=close_notification, sent_by="ADM")
        self.assertFalse(mock_email.called)
        self.assertFalse(mock_text.called)
        self.assertFalse(mock_push_notification.called)

    def test_dont_resend_alert(self, mock_email, mock_text, mock_push_notification):
        self.dont_resend_alert_helper(
            mock_email, mock_text, mock_push_notification, close_notification=False
        )

    def test_dont_resend_close_notification(self, mock_email, mock_text, mock_push_notification):
        self.dont_resend_alert_helper(
            mock_email, mock_text, mock_push_notification, close_notification=True
        )

    def resend_alert_forced_helper(
        self,
        mock_email,
        mock_text,
        mock_push_notification,
        push_notification,
        close_notification,
    ):
        """
        This helper checks that calling tasks.send_alert with the forced parameter as True
        will send an alert even if an alert has already been sent for that registration, in
        4 possible cases.  Either push notifications are enabled or disabled (push_notification
        is True or False), and the alert is either normal or it is a close notification
        (close_notification is True or False).
        """
        self.r.user.profile.push_notifications = push_notification
        self.r.user.profile.save()
        self.r.close_notification = close_notification
        self.r.notification_sent = True
        self.r.close_notification_sent = True
        self.r.save()
        self.r.alert(True)
        self.assertTrue(mock_email.called)
        self.assertEquals(not push_notification, mock_text.called)
        self.assertEquals(push_notification, mock_push_notification.called)

    def test_resend_alert_forced(self, mock_email, mock_text, mock_push_notification):
        self.resend_alert_forced_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=False,
            close_notification=False,
        )

    def test_resend_alert_forced_push(self, mock_email, mock_text, mock_push_notification):
        self.resend_alert_forced_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=True,
            close_notification=False,
        )

    def test_resend_close_notification_forced(self, mock_email, mock_text, mock_push_notification):
        self.resend_alert_forced_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=False,
            close_notification=True,
        )

    def test_resend_close_notification_forced_push(
        self, mock_email, mock_text, mock_push_notification
    ):
        self.resend_alert_forced_helper(
            mock_email,
            mock_text,
            mock_push_notification,
            push_notification=True,
            close_notification=True,
        )


class RegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.sections = []
        self.sections.append(get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-1600-002", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)[1])

    def test_successful_registration(self):
        res, norm, _ = register_for_course(
            self.sections[0].full_code, "e@example.com", "+15555555555"
        )
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual(self.sections[0].full_code, r.section.full_code)
        self.assertEqual("e@example.com", r.email)
        self.assertEqual("+15555555555", r.phone)
        self.assertFalse(r.notification_sent)
        self.assertEqual(SOURCE_PCA, r.source)
        self.assertIsNone(r.api_key)

    def test_nonnormalized_course_code(self):
        res, norm, _ = register_for_course("cis1600001", "e@example.com", "+15555555555")
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual("CIS-1600-001", norm)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual("CIS-1600-001", r.section.full_code)

    def test_duplicate_registration(self):
        r1 = Registration(email="e@example.com", phone="+15555555555", section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(
            self.sections[0].full_code, "e@example.com", "+15555555555"
        )
        self.assertEqual(RegStatus.OPEN_REG_EXISTS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_reregister(self):
        r1 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.sections[0],
            notification_sent=True,
        )
        r1.save()
        res, norm, _ = register_for_course(
            self.sections[0].full_code, "e@example.com", "+15555555555"
        )
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffsections(self):
        r1 = Registration(email="e@example.com", phone="+15555555555", section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(
            self.sections[1].full_code, "e@example.com", "+15555555555"
        )
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffcourse(self):
        r1 = Registration(email="e@example.com", phone="+15555555555", section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(
            self.sections[2].full_code, "e@example.com", "+15555555555"
        )
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_justemail(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, "e@example.com", None)
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_phony_course(self):
        res, norm, _ = register_for_course("PHONY-100-001", "e@example.com", "+15555555555")
        self.assertEqual(RegStatus.COURSE_NOT_FOUND, res)
        self.assertEqual(0, Registration.objects.count())

    def test_invalid_course(self):
        res, norm, _ = register_for_course("econ 0-0-1", "e@example.com", "+15555555555")
        self.assertEqual(RegStatus.COURSE_NOT_FOUND, res)
        self.assertEqual(0, Registration.objects.count())

    def test_justphone(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, None, "5555555555")
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_nocontact(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, None, None)
        self.assertEqual(RegStatus.NO_CONTACT_INFO, res)
        self.assertEqual(0, len(Registration.objects.all()))

    def test_nocontact_new(self):
        user = User.objects.create_user(username="new_jacob", password="top_secret")
        user.save()
        new_client = APIClient()
        new_client.login(username="new_jacob", password="top_secret")
        user = User.objects.get(username="new_jacob")
        self.assertIsNone(user.profile.email)
        self.assertIsNone(user.profile.phone)
        self.assertFalse(user.profile.push_notifications)
        res, norm, _ = register_for_course(self.sections[0].full_code, user=user)
        self.assertEqual(RegStatus.NO_CONTACT_INFO, res)
        self.assertEqual(0, len(Registration.objects.all()))


class ResubscribeTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section, _, _ = get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)
        self.base_reg = Registration(
            email="e@example.com", phone="+15555555555", section=self.section
        )
        self.base_reg.save()

    def test_resubscribe(self):
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg = self.base_reg.resubscribe()
        self.assertNotEqual(reg, self.base_reg)
        self.assertEqual(self.base_reg, reg.resubscribed_from)

    def test_try_resubscribe_noalert(self):
        reg = self.base_reg.resubscribe()
        self.assertEqual(reg, self.base_reg)
        self.assertIsNone(reg.resubscribed_from)

    def test_resubscribe_oldlink(self):
        """following the resubscribe chain from an old link"""
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg1 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.section,
            resubscribed_from=self.base_reg,
            notification_sent=True,
        )
        reg1.save()
        reg2 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.section,
            resubscribed_from=reg1,
            notification_sent=True,
        )
        reg2.save()
        self.base_reg.head_registration = reg2
        self.base_reg.save()
        reg1.head_registration = reg2
        reg1.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result.resubscribed_from, reg2)

    def test_resubscribe_oldlink_noalert(self):
        """testing idempotence on old links"""
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg1 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.section,
            resubscribed_from=self.base_reg,
            notification_sent=True,
        )
        reg1.save()
        reg2 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.section,
            resubscribed_from=reg1,
            notification_sent=True,
        )
        reg2.save()
        reg3 = Registration(
            email="e@example.com",
            phone="+15555555555",
            section=self.section,
            resubscribed_from=reg2,
            notification_sent=False,
        )
        reg3.save()
        self.base_reg.head_registration = reg3
        self.base_reg.save()
        reg1.head_registration = reg3
        reg1.save()
        reg2.head_registration = reg3
        reg2.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result, reg3)


class WebhookTriggeredAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section, _, _ = get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)
        self.r1 = Registration(email="e@example.com", phone="+15555555555", section=self.section)
        self.r2 = Registration(email="f@example.com", phone="+15555555556", section=self.section)
        self.r3 = Registration(email="g@example.com", phone="+15555555557", section=self.section)
        self.r1.save()
        self.r2.save()
        self.r3.save()

    def test_collect_all(self):
        result = tasks.get_registrations_for_alerts(self.section.full_code, TEST_SEMESTER)
        expected_ids = [r.id for r in [self.r1, self.r2, self.r3]]
        result_ids = [r.id for r in result]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)

        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_none(self):
        get_or_create_course_and_section("CIS-1210-001", TEST_SEMESTER)
        result = tasks.get_registrations_for_alerts("CIS-1210-001", TEST_SEMESTER)
        self.assertTrue(len(result) == 0)

    def test_collect_one(self):
        self.r2.notification_sent = True
        self.r3.notification_sent = True
        self.r2.save()
        self.r3.save()
        result_ids = [
            r.id for r in tasks.get_registrations_for_alerts(self.section.full_code, TEST_SEMESTER)
        ]
        expected_ids = [self.r1.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_some(self):
        self.r2.notification_sent = True
        self.r2.save()
        result_ids = [
            r.id for r in tasks.get_registrations_for_alerts(self.section.full_code, TEST_SEMESTER)
        ]
        expected_ids = [self.r1.id, self.r3.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)


@patch("alert.views.alert_for_course")
class WebhookViewTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.client = Client()
        auth = base64.standard_b64encode("webhook:password".encode("ascii"))
        self.headers = {
            "Authorization": f"Basic {auth.decode()}",
        }
        self.body = {
            "section_id_normalized": "ANTH-3610-401",
            "previous_status": "X",
            "status": "O",
            "status_code_normalized": "Open",
            "term": translate_semester(TEST_SEMESTER),
        }
        Option.objects.update_or_create(
            key="SEND_FROM_WEBHOOK", value_type="BOOL", defaults={"value": "TRUE"}
        )

    def test_alert_called_and_sent_intl(self, mock_alert):
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(
                {
                    "section_id_normalized": "INTL-BUL-001",
                    "previous_status": "X",
                    "status": "O",
                    "status_code_normalized": "Open",
                    "term": translate_semester(TEST_SEMESTER),
                }
            ),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertTrue(mock_alert.called)
        self.assertEqual("INTL-BUL-001", mock_alert.call_args[0][0])
        self.assertEqual("2019A", mock_alert.call_args[1]["semester"])
        self.assertEqual("O", mock_alert.call_args[1]["course_status"])
        self.assertTrue("sent" in json.loads(res.content)["message"])
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertTrue(u.alert_sent)

    def test_alert_called_and_sent(self, mock_alert):
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertTrue(mock_alert.called)
        self.assertEqual("ANTH-3610-401", mock_alert.call_args[0][0])
        self.assertEqual("2019A", mock_alert.call_args[1]["semester"])
        self.assertEqual("O", mock_alert.call_args[1]["course_status"])
        self.assertTrue("sent" in json.loads(res.content)["message"])
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertTrue(u.alert_sent)

    def test_alert_bad_json(self, mock_alert):
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data="blah",
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_alert_called_closed_course(self, mock_alert):
        self.body["status"] = "C"
        self.body["status_code_normalized"] = "Closed"
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertTrue("sent" in json.loads(res.content)["message"])
        self.assertTrue(mock_alert.called)
        self.assertEqual("C", mock_alert.call_args[1]["course_status"])
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertTrue(u.alert_sent)

    def test_alert_called_wrong_sem(self, mock_alert):
        self.body["term"] = "NOTRM"
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertFalse(
            "sent" in json.loads(res.content)["message"],
        )
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_alert_called_alerts_off(self, mock_alert):
        Option.objects.update_or_create(
            key="SEND_FROM_WEBHOOK", value_type="BOOL", defaults={"value": "FALSE"}
        )
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertFalse("sent" in json.loads(res.content)["message"])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_after_adp(self, mock_alert):
        current_adp = get_add_drop_period(semester=TEST_SEMESTER)
        current_adp.end = datetime.utcnow().replace(tzinfo=gettz(TIME_ZONE)) - timedelta(days=1)
        current_adp.save()
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertFalse("sent" in json.loads(res.content)["message"])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_not_current_semester(self, mock_alert):
        self.body["term"] = "3021C"
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertFalse("sent" in json.loads(res.content)["message"])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_bad_format(self, mock_alert):
        self.body = {"hello": "world"}
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps({"hello": "world"}),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_no_status(self, mock_alert):
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(
                {
                    "section_id_normalized": "ANTH-3610-401",
                    "previous_status": "X",
                    "status_code_normalized": "Open",
                    "term": translate_semester("2019A"),
                }
            ),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_method(self, mock_alert):
        res = self.client.get(reverse("webhook", urlconf="alert.urls"), **self.headers)
        self.assertEqual(405, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_content(self, mock_alert):
        res = self.client.post(reverse("webhook", urlconf="alert.urls"), **self.headers)
        self.assertEqual(415, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_password(self, mock_alert):
        self.headers["Authorization"] = (
            "Basic " + base64.standard_b64encode("webhook:abc123".encode("ascii")).decode()
        )
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(200, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_user(self, mock_alert):
        self.headers["Authorization"] = (
            "Basic " + base64.standard_b64encode("baduser:password".encode("ascii")).decode()
        )
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(self.body),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(200, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())


class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        adp = get_add_drop_period(TEST_SEMESTER)
        start = adp.estimated_start
        end = adp.estimated_end
        duration = end - start
        _, cis1200_section = create_mock_data("CIS-1200-001", TEST_SEMESTER)
        _, cis1600_section = create_mock_data("CIS-1600-001", TEST_SEMESTER)
        self.statusUpdates = [
            StatusUpdate(
                created_at=start - duration / 4,
                section=cis1200_section,
                old_status="C",
                new_status="O",
                alert_sent=False,
            ),
            StatusUpdate(
                created_at=start + duration / 4,
                section=cis1200_section,
                old_status="O",
                new_status="C",
                alert_sent=False,
            ),
            StatusUpdate(
                created_at=start + duration / 2,
                section=cis1200_section,
                old_status="C",
                new_status="O",
                alert_sent=True,
            ),
            StatusUpdate(
                created_at=start + 3 * duration / 4,
                section=cis1600_section,
                old_status="C",
                new_status="O",
                alert_sent=True,
            ),
            StatusUpdate(
                created_at=end + duration / 4,
                section=cis1600_section,
                old_status="O",
                new_status="C",
                alert_sent=False,
            ),
        ]
        for s in self.statusUpdates:
            s.save()
        self.client = APIClient()

    def test_cis1200(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-1200-001"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[0]["old_status"], "O")
        self.assertEqual(response.data[0]["new_status"], "C")
        self.assertEqual(response.data[0]["alert_sent"], False)
        self.assertFalse(hasattr(response.data[0], "request_body"))
        self.assertEqual(response.data[1]["old_status"], "C")
        self.assertEqual(response.data[1]["new_status"], "O")
        self.assertEqual(response.data[1]["alert_sent"], True)
        self.assertFalse(hasattr(response.data[1], "request_body"))

    def test_cis1600(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-1600-001"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["old_status"], "C")
        self.assertEqual(response.data[0]["new_status"], "O")
        self.assertEqual(response.data[0]["alert_sent"], True)
        self.assertFalse(hasattr(response.data[0], "request_body"))

    def test_cis1210_missing(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-1210"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@ddt
class AlertRegistrationTestCase(TestCase):
    def setUp(self):
        set_semester()
        Option.objects.update_or_create(
            key="SEND_FROM_WEBHOOK", value_type="BOOL", defaults={"value": "TRUE"}
        )
        self.user = User.objects.create_user(username="jacob", password="top_secret")
        self.user.save()
        self.user.profile.email = "j@gmail.com"
        self.user.profile.phone = "+19178286431"
        self.user.profile.save()
        self.user = User.objects.get(username="jacob")
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")
        _, self.cis1200 = create_mock_data("CIS-1200-001", TEST_SEMESTER)
        _, self.cis1600 = create_mock_data("CIS-1600-001", TEST_SEMESTER)
        _, self.cis1210 = create_mock_data("CIS-1210-001", TEST_SEMESTER)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        self.registration_cis1200 = Registration.objects.get(section=self.cis1200)

    @staticmethod
    def convert_date(date):
        return parse_datetime(date) if date is not None else None

    def check_model_with_response_data(self, model, data):
        self.assertEqual(model.id, data["id"])
        self.assertEqual(model.user.username, data["user"])
        self.assertEqual(model.is_active, data["is_active"])
        self.assertEqual(model.section.full_code, data["section"])
        self.assertEqual(model.deleted, data["deleted"])
        self.assertEqual(model.deleted_at, self.convert_date(data["deleted_at"]))
        self.assertEqual(model.auto_resubscribe, data["auto_resubscribe"])
        self.assertEqual(model.notification_sent, data["notification_sent"])
        self.assertEqual(
            model.notification_sent_at, self.convert_date(data["notification_sent_at"])
        )
        self.assertEqual(model.close_notification, data["close_notification"])
        self.assertEqual(model.close_notification_sent, data["close_notification_sent"])
        self.assertEqual(
            model.close_notification_sent_at,
            self.convert_date(data["close_notification_sent_at"]),
        )
        self.assertEqual(model.original_created_at, self.convert_date(data["original_created_at"]))
        self.assertEqual(model.created_at, self.convert_date(data["created_at"]))
        self.assertEqual(model.updated_at, self.convert_date(data["updated_at"]))

    def simulate_alert_helper_before(self, section, from_status="X", to_status="O"):
        """
        This helper is run before simulate_alert is run, with all the proper functions mocked.
        This is what actually simulates the webook action.
        """
        auth = base64.standard_b64encode("webhook:password".encode("ascii"))
        headers = {
            "Authorization": f"Basic {auth.decode()}",
        }
        body = {
            "section_id_normalized": section.full_code,
            "previous_status": from_status,
            "status": to_status,
            "status_code_normalized": "Open",
            "term": translate_semester(section.semester),
        }
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(body),
            content_type="application/json",
            **headers,
        )
        self.assertEqual(200, res.status_code)
        self.assertTrue("sent" in json.loads(res.content)["message"])

    def simulate_alert(
        self,
        section,
        num_status_updates=None,
        contact_infos=None,
        should_send=True,
        close_notification=False,
    ):
        """
        This helper simulates a webhook status update for a class opening (if close_notification is
        false), or for a class closing (if close_notification is True). It simulates the working
        of the entire system by mocking the alerts.send_email, alerts.send_text, and
        requests.post (the function used for sending push notifications) functions. Note that it
        does NOT test the aforementioned functions, but rather ensures that they are called as
        specified.  Specifically, by default it will ensure they are called for the default
        user's contact information. However, you can customize this check by passing in a list
        of dictionaries (see the default contact_infos dict for an example of the proper schema).
        This function will ensure that for each specified contact, the proper notification
        function is called with the proper contact information. Also, you can specify whether
        the webhook should cause an alert to be sent at all with the should_send parameter.
        Finally, you can specify how many cumulative Status Updates objects should be saved in the
        database after this webhook status update is triggered by using the num_status_updates
        parameter.
        """
        contact_infos = (
            # If we enabled push notifications by default in these tests, push_username would be
            # set to "jacob", since that is the username of the default user for these tests.
            [{"number": "+19178286431", "email": "j@gmail.com", "push_username": None}]
            if contact_infos is None
            else contact_infos
        )
        # ensure no duplicate contact info in contact_infos list
        for i, c in enumerate(contact_infos):
            for j in range(i + 1, len(contact_infos)):
                if (
                    contact_infos[j]["number"] == c["number"]
                    or contact_infos[j]["email"] == c["email"]
                ):
                    raise ValueError(
                        "Duplicate contact information found in contact_infos list between "
                        f"{c} and {contact_infos[j]}."
                    )

        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code

        active_registration_ids = [
            reg.id
            for reg in list(
                Registration.objects.filter(section=section, **Registration.is_active_filter())
            )
        ]
        waiting_for_close_registration_ids = [
            reg.id
            for reg in list(
                Registration.objects.filter(
                    section=section, **Registration.is_waiting_for_close_filter()
                )
            )
        ]

        with patch("alert.alerts.send_email", return_value=True) as send_email_mock:
            with patch("alert.alerts.send_text", return_value=True) as send_text_mock:
                with patch(
                    "requests.post", return_value=MockResponse(200)
                ) as push_notification_mock:
                    override_delay(
                        [
                            ("alert.tasks", "send_course_alerts"),
                            ("alert.tasks", "send_alert"),
                        ],
                        self.simulate_alert_helper_before,
                        {
                            "section": section,
                            "from_status": ("C" if not close_notification else "O"),
                            "to_status": ("O" if not close_notification else "C"),
                        },
                    )
                    self.assertEqual(
                        (
                            0
                            if not should_send
                            else len(
                                [c for c in contact_infos if "email" in c.keys() and c["email"]]
                            )
                        ),
                        send_email_mock.call_count,
                    )
                    self.assertEqual(
                        (
                            0
                            if not should_send
                            else len(
                                [
                                    c
                                    for c in contact_infos
                                    if "number" in c.keys()
                                    and c["number"]
                                    and ("push_username" not in c.keys() or not c["push_username"])
                                ]
                            )
                        ),
                        send_text_mock.call_count,
                    )
                    self.assertEqual(
                        (
                            0
                            if not should_send
                            else len(
                                [
                                    c
                                    for c in contact_infos
                                    if "push_username" in c.keys() and c["push_username"]
                                ]
                            )
                        ),
                        push_notification_mock.call_count,
                    )
                    for c in contact_infos:
                        self.assertEqual(
                            (
                                0
                                if not should_send or "email" not in c.keys() or not c["email"]
                                else 1
                            ),
                            len(
                                [
                                    m
                                    for m in send_email_mock.call_args_list
                                    if "email" in c.keys() and m[1]["to"] == c["email"]
                                ]
                            ),
                        )
                        self.assertEqual(
                            (
                                0
                                if not should_send
                                or "number" not in c.keys()
                                or not c["number"]
                                or ("push_username" in c.keys() and c["push_username"])
                                else 1
                            ),
                            len(
                                [
                                    m
                                    for m in send_text_mock.call_args_list
                                    if "number" in c.keys() and m[0][0] == c["number"]
                                ]
                            ),
                        )
                        self.assertEqual(
                            (
                                0
                                if not should_send
                                or "push_username" not in c.keys()
                                or not c["push_username"]
                                else 1
                            ),
                            len(
                                [
                                    m
                                    for m in push_notification_mock.call_args_list
                                    if "push_username" in c.keys()
                                    and m[1]["data"]["pennkey"] == c["push_username"]
                                ]
                            ),
                        )
                    if not close_notification:
                        for r_id in active_registration_ids:
                            r = Registration.objects.get(id=r_id)
                            self.assertEquals(should_send, r.notification_sent)
                            if should_send:
                                self.assertIsNotNone(r.notification_sent_at)
                            else:
                                self.assertNone(r.notification_sent_at)
                    else:
                        for r_id in waiting_for_close_registration_ids:
                            r = Registration.objects.get(id=r_id)
                            self.assertEquals(should_send, r.close_notification_sent)
                            if should_send:
                                self.assertIsNotNone(r.close_notification_sent_at)
                            else:
                                self.assertNone(r.close_notification_sent_at)
                    if num_status_updates is not None:
                        self.assertEqual(num_status_updates, StatusUpdate.objects.count())
                    for u in StatusUpdate.objects.all():
                        self.assertTrue(u.alert_sent)

    def create_resubscribe_group(self, close_notifications=False):
        """
        Resubscribe chains created:
        first -> third -> fourth (CIS-1200-001)
        second (CIS-1600-001)
        fifth (CIS-1210-001)
        """
        first_id = self.registration_cis1200.id
        self.assertEqual(self.registration_cis1200.head_registration, self.registration_cis1200)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        second_id = response.data["id"]
        second_ob = Registration.objects.get(id=second_id)
        self.assertEqual(second_ob.head_registration, second_ob)

        response = self.client.get(reverse("registrations-detail", args=[second_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=second_id), response.data)
        self.simulate_alert(self.cis1200, 1)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"id": first_id, "resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        third_id = response.data["id"]
        third_ob = Registration.objects.get(id=third_id)
        self.assertEqual(third_ob.head_registration, third_ob)
        second_ob = Registration.objects.get(id=second_id)
        self.assertEqual(second_ob.head_registration, second_ob)
        first_ob = Registration.objects.get(id=first_id)
        self.assertEqual(first_ob.head_registration, third_ob)

        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(
            self.registration_cis1200.resubscribed_to, response.data
        )
        self.simulate_alert(
            self.cis1200, 2, close_notification=True, should_send=close_notifications
        )
        self.simulate_alert(self.cis1200, 3)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"id": third_id, "resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        fourth_id = response.data["id"]
        fourth_ob = Registration.objects.get(id=fourth_id)
        self.assertEqual(fourth_ob.head_registration, fourth_ob)
        third_ob = Registration.objects.get(id=third_id)
        self.assertEqual(third_ob.head_registration, fourth_ob)
        second_ob = Registration.objects.get(id=second_id)
        self.assertEqual(second_ob.head_registration, second_ob)
        first_ob = Registration.objects.get(id=first_id)
        self.assertEqual(first_ob.head_registration, fourth_ob)

        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1210-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

        fifth_id = response.data["id"]
        fifth_ob = Registration.objects.get(id=fifth_id)
        self.assertEqual(fifth_ob.head_registration, fifth_ob)

        # first is original CIS1200 registration, second is disconnected CIS1600 registration,
        # third is resubscribed from first, fourth is resubscribed from third,
        # and fifth is disconnected CIS1210 registration
        return {
            "first_id": first_id,
            "second_id": second_id,
            "third_id": third_id,
            "fourth_id": fourth_id,
            "fifth_id": fifth_id,
        }

    def create_auto_resubscribe_group(self, put=False, close_notifications=False):
        """
        Resubscribe chains created:
        first -> third -> fourth (CIS-1200-001)
        second (CIS-1600-001)
        fifth (CIS-1210-001)
        """
        first_id = self.registration_cis1200.id
        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"auto_resubscribe": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "auto_resubscribe": True}),
                content_type="application/json",
            )
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse("registrations-detail", args=[first_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=first_id), response.data)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        second_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[second_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=second_id), response.data)
        self.simulate_alert(self.cis1200, 1)
        first_ob = Registration.objects.get(id=first_id)
        third_ob = first_ob.resubscribed_to
        third_id = third_ob.id
        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(third_ob, response.data)
        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(third_ob, response.data)
        self.simulate_alert(
            self.cis1200, 2, close_notification=True, should_send=close_notifications
        )
        self.simulate_alert(self.cis1200, 3)
        first_ob = Registration.objects.get(id=first_id)
        third_ob = first_ob.resubscribed_to
        fourth_ob = third_ob.resubscribed_to
        fourth_id = fourth_ob.id
        response = self.client.get(reverse("registrations-detail", args=[fourth_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(fourth_ob, response.data)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1210-001", "auto_resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        fifth_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[fifth_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=fifth_id), response.data)
        # first is original CIS1200 registration, second is disconnected CIS1600 registration,
        # third is auto-resubscribed from first, fourth is auto-resubscribed from third,
        # and fifth is disconnected CIS1210 registration
        return {
            "first_id": first_id,
            "second_id": second_id,
            "third_id": third_id,
            "fourth_id": fourth_id,
            "fifth_id": fifth_id,
        }

    def test_registrations_get_simple(self):
        response = self.client.get(
            reverse("registrations-detail", args=[self.registration_cis1200.pk])
        )
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(self.registration_cis1200, response.data)

    def test_semester_not_set(self):
        Option.objects.filter(key="SEMESTER").delete()
        cache.delete("SEMESTER")
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(500, response.status_code)
        self.assertTrue("SEMESTER" in response.data["detail"])

    def test_registrations_get_only_current_semester(self):
        _, self.cis110in2019C = create_mock_data("CIS-1100-001", "2019C")
        registration = Registration(section=self.cis110in2019C, user=self.user, source="PCA")
        registration.auto_resubscribe = False
        registration.save()
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(
            Registration.objects.get(section=self.cis1200), response.data[0]
        )

    def test_registration_history_get_only_current_semester(self):
        _, self.cis110in2019C = create_mock_data("CIS-1100-001", "2019C")
        registration = Registration(section=self.cis110in2019C, user=self.user, source="PCA")
        registration.auto_resubscribe = False
        registration.save()
        response = self.client.get(reverse("registrationhistory-list"))
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(
            Registration.objects.get(section=self.cis1200), response.data[0]
        )

    def registrations_resubscribe_get_old_and_history_helper(self, ids):
        """
        This helper tests the GET Registrations route and GET Registration History, using the
        passed in Registration ids.
        """
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        fourth_data = next(item for item in response.data if item["id"] == ids["fourth_id"])
        second_data = next(item for item in response.data if item["id"] == ids["second_id"])
        fifth_data = next(item for item in response.data if item["id"] == ids["fifth_id"])
        self.check_model_with_response_data(
            self.registration_cis1200.resubscribed_to.resubscribed_to, fourth_data
        )
        self.check_model_with_response_data(
            Registration.objects.get(id=ids["second_id"]), second_data
        )
        self.check_model_with_response_data(
            Registration.objects.get(id=ids["fifth_id"]), fifth_data
        )
        response = self.client.get(reverse("registrationhistory-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(5, len(response.data))
        first_data = next(item for item in response.data if item["id"] == ids["first_id"])
        first_ob = Registration.objects.get(id=ids["first_id"])
        self.assertEqual(first_ob.created_at, self.convert_date(first_data["original_created_at"]))
        self.check_model_with_response_data(first_ob, first_data)
        self.assertIsNone(first_ob.resubscribed_from)
        self.assertTrue(first_ob.notification_sent)
        self.assertIsNotNone(first_ob.notification_sent_at)
        second_data = next(item for item in response.data if item["id"] == ids["second_id"])
        second_ob = Registration.objects.get(id=ids["second_id"])
        self.assertEqual(
            second_ob.created_at, self.convert_date(second_data["original_created_at"])
        )
        self.check_model_with_response_data(second_ob, second_data)
        self.assertIsNone(second_ob.resubscribed_from)
        self.assertFalse(hasattr(second_ob, "resubscribed_to"))
        self.assertFalse(second_data["notification_sent"])
        self.assertIsNone(second_data["notification_sent_at"])
        third_data = next(item for item in response.data if item["id"] == ids["third_id"])
        third_ob = Registration.objects.get(id=ids["third_id"])
        self.assertEqual(
            self.registration_cis1200.resubscribed_to,
            Registration.objects.get(id=ids["third_id"]),
        )
        self.assertEqual(first_ob, third_ob.resubscribed_from)
        self.assertEqual(first_ob.created_at, self.convert_date(third_data["original_created_at"]))
        self.check_model_with_response_data(first_ob.resubscribed_to, third_data)
        self.assertTrue(third_data["notification_sent"])
        self.assertIsNotNone(third_data["notification_sent_at"])
        fourth_data = next(item for item in response.data if item["id"] == ids["fourth_id"])
        fourth_ob = Registration.objects.get(id=ids["fourth_id"])
        self.assertEqual(first_ob.resubscribed_to.resubscribed_to, fourth_ob)
        self.assertEqual(first_ob.created_at, self.convert_date(fourth_data["original_created_at"]))
        self.check_model_with_response_data(first_ob.resubscribed_to.resubscribed_to, fourth_data)
        self.assertEqual(third_ob, fourth_ob.resubscribed_from)
        self.assertFalse(hasattr(fourth_ob, "resubscribed_to"))
        self.assertFalse(fourth_data["notification_sent"])
        self.assertIsNone(fourth_data["notification_sent_at"])
        fifth_data = next(item for item in response.data if item["id"] == ids["fifth_id"])
        fifth_ob = Registration.objects.get(id=ids["fifth_id"])
        self.assertEqual(fifth_ob.created_at, self.convert_date(fifth_data["original_created_at"]))
        self.check_model_with_response_data(fifth_ob, fifth_data)
        self.assertIsNone(fifth_ob.resubscribed_from)
        self.assertFalse(hasattr(fifth_ob, "resubscribed_to"))
        self.assertFalse(fifth_data["notification_sent"])
        self.assertIsNone(fifth_data["notification_sent_at"])

    def test_registrations_resubscribe_get_old_and_history(self):
        ids = self.create_resubscribe_group()
        self.registrations_resubscribe_get_old_and_history_helper(ids)

    def test_registrations_resubscribe_get_old_and_history_autoresub(self):
        ids = self.create_auto_resubscribe_group()
        self.registrations_resubscribe_get_old_and_history_helper(ids)

    def resubscribe_to_old_helper(self, ids, auto_resub=False):
        """
        This helper tests that resubscribing to an old alert still adds to the head of the
        resubscribe chain, in two cases.  Either auto_resub is False (in which case
        the function manually resubscribes to an old registration), or auto_resub is True
        (in which case the registration auto-resubscribes itself).
        """
        first_ob = Registration.objects.get(id=ids["first_id"])
        fourth_ob = Registration.objects.get(id=ids["fourth_id"])
        self.simulate_alert(self.cis1200, 4, close_notification=True, should_send=False)
        self.simulate_alert(self.cis1200, 5)
        if auto_resub:
            sixth_id = Registration.objects.get(id=ids["fourth_id"]).resubscribed_to.id
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": ids["third_id"], "resubscribe": True}),
                content_type="application/json",
            )
            self.assertEqual(200, response.status_code)
            sixth_id = response.data["id"]
        response = self.client.get(reverse("registrations-list"))
        sixth_data = next(item for item in response.data if item["id"] == sixth_id)
        sixth_ob = Registration.objects.get(id=sixth_id)
        self.assertEqual(fourth_ob.resubscribed_to, sixth_ob)
        self.assertEqual(first_ob.created_at, self.convert_date(sixth_data["original_created_at"]))
        self.check_model_with_response_data(fourth_ob.resubscribed_to, sixth_data)
        self.assertEqual(fourth_ob, sixth_ob.resubscribed_from)
        self.assertFalse(hasattr(sixth_ob, "resubscribed_to"))
        self.assertFalse(sixth_data["notification_sent"])
        self.assertIsNone(sixth_data["notification_sent_at"])

    def test_resubscribe_to_old(self):
        ids = self.create_resubscribe_group()
        self.resubscribe_to_old_helper(ids)

    def test_resubscribe_to_old_auto_resub(self):
        ids = self.create_auto_resubscribe_group()
        self.resubscribe_to_old_helper(ids, True)

    def test_register_for_existing(self):
        self.create_resubscribe_group()
        num = Registration.objects.count()
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(409, response.status_code)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual(num, Registration.objects.count())

    def test_register_no_contact(self):
        self.user.profile.email = None
        self.user.profile.phone = None
        self.user.profile.push_notifications = False
        self.user.save()
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(406, response.status_code)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1210-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(406, response.status_code)
        self.assertEqual(1, Registration.objects.count())

    def push_notification_simple_test(self):
        new_user = User.objects.create_user(username="new_jacob", password="top_secret")
        new_user.save()
        new_user.profile.email = "newj@gmail.com"
        new_user.profile.phone = "+12234567890"
        new_user.profile.push_notifications = True
        new_user.profile.save()
        new_client = APIClient()
        new_client.login(username="new_jacob", password="top_secret")
        new_user = User.objects.get(username="new_jacob")
        create_mock_data("CIS-1920-201", TEST_SEMESTER)
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1920-201", "auto_resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        new_first_id = response.data["id"]
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        new_second_id = response.data["id"]
        self.simulate_alert(
            "CIS-1920-201",
            num_status_updates=1,
            contact_infos=[
                {
                    "number": new_user.profile.phone,
                    "email": new_user.profile.email,
                    "push_username": new_user.username,
                }
            ],
            should_send=True,
            close_notification=False,
        )
        self.simulate_alert(
            "CIS-1200-201",
            num_status_updates=1,
            contact_infos=[
                {
                    "number": new_user.profile.phone,
                    "email": new_user.profile.email,
                    "push_username": new_user.username,
                },
                {
                    "number": "+19178286431",
                    "email": "j@gmail.com",
                    "push_username": None,
                },
            ],
            should_send=True,
            close_notification=False,
        )
        self.assertTrue(Registration.objects.get(id=new_first_id).notification_sent)
        self.assertIsNotNone(Registration.objects.get(id=new_first_id).resubscribed_to)
        self.assertFalse(Registration.objects.get(id=new_second_id).notification_sent)
        self.assertIsNone(Registration.objects.get(id=new_second_id).resubscribed_to)

    def registrations_multiple_users_helper(self, ids, auto_resub=False):
        """
        This helper tests that proper functionality occurs even with multiple users in the DB.
        It runs for the given set of registration ids, and enables or disables auto resubscribe
        depending on the auto_resub parameter.
        """
        new_user = User.objects.create_user(username="new_jacob", password="top_secret")
        new_user.save()
        new_user.profile.email = "newj@gmail.com"
        new_user.profile.phone = "+12234567890"
        new_user.profile.save()
        new_client = APIClient()
        new_client.login(username="new_jacob", password="top_secret")
        create_mock_data("CIS-1920-201", TEST_SEMESTER)
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1920-201", "auto_resubscribe": auto_resub}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        new_first_id = response.data["id"]
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": auto_resub}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        new_second_id = response.data["id"]
        response = new_client.get(reverse("registrations-list"))
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        new_first_data = next(item for item in response.data if item["id"] == new_first_id)
        new_first_ob = Registration.objects.get(id=new_first_id)
        self.check_model_with_response_data(new_first_ob, new_first_data)
        new_second_data = next(item for item in response.data if item["id"] == new_second_id)
        new_second_ob = Registration.objects.get(id=new_second_id)
        self.check_model_with_response_data(new_second_ob, new_second_data)
        response = new_client.get(reverse("registrationhistory-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            0,
            len([item for item in response.data if item["id"] in [id for id in ids.values()]]),
        )
        self.assertEqual(2, len(response.data))
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_first_id]))
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_second_id]))
        self.assertEqual(3, len(response.data))
        response = self.client.get(reverse("registrationhistory-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_first_id]))
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_second_id]))
        self.assertEqual(5, len(response.data))
        # now test resubscribing with multiple users and alerts for multiple users
        self.simulate_alert(self.cis1200, 4, close_notification=True, should_send=False)
        self.simulate_alert(
            self.cis1200,
            5,
            [
                {"number": "+19178286431", "email": "j@gmail.com"},
                {"number": "+12234567890", "email": "newj@gmail.com"},
            ],
        )
        if auto_resub:
            sixth_id = Registration.objects.get(id=ids["fourth_id"]).resubscribed_to.id
            new_third_id = Registration.objects.get(id=new_second_id).resubscribed_to.id
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": ids["fourth_id"], "resubscribe": True}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            sixth_id = response.data["id"]
            response = new_client.post(
                reverse("registrations-list"),
                json.dumps({"id": new_second_id, "resubscribe": True}),
                content_type="application/json",
            )
            self.assertEqual(200, response.status_code)
            new_third_id = response.data["id"]
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(3, len(response.data))
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_first_id]))
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_second_id]))
        sixth_data = next(item for item in response.data if item["id"] == sixth_id)
        sixth_ob = Registration.objects.get(id=sixth_id)
        self.check_model_with_response_data(sixth_ob, sixth_data)
        self.assertEqual(Registration.objects.get(id=ids["fourth_id"]), sixth_ob.resubscribed_from)
        self.assertFalse(hasattr(sixth_ob, "resubscribed_to"))
        self.assertFalse(sixth_data["notification_sent"])
        self.assertIsNone(sixth_data["notification_sent_at"])
        response = self.client.get(reverse("registrationhistory-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_first_id]))
        self.assertEqual(0, len([item for item in response.data if item["id"] == new_second_id]))
        self.assertEqual(6, len(response.data))
        response = new_client.get(reverse("registrations-list"))
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        next(item for item in response.data if item["id"] == new_third_id)
        new_third_data = next(item for item in response.data if item["id"] == new_third_id)
        new_third_ob = Registration.objects.get(id=new_third_id)
        self.check_model_with_response_data(new_third_ob, new_third_data)
        self.assertEqual(Registration.objects.get(id=new_second_id), new_third_ob.resubscribed_from)
        self.assertFalse(hasattr(new_third_ob, "resubscribed_to"))
        self.assertFalse(new_third_data["notification_sent"])
        self.assertIsNone(new_third_data["notification_sent_at"])
        response = new_client.get(reverse("registrationhistory-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            0,
            len([item for item in response.data if item["id"] in [id for id in ids.values()]]),
        )
        self.assertEqual(3, len(response.data))

    def test_registrations_multiple_users(self):
        ids = self.create_resubscribe_group()
        self.registrations_multiple_users_helper(ids)

    def test_registrations_multiple_users_id_isolation(self):
        ids = self.create_resubscribe_group()
        new_user = User.objects.create_user(username="new_jacob", password="top_secret")
        new_user.save()
        new_user.profile.email = "newj@gmail.com"
        new_user.profile.phone = "+12234567890"
        new_user.profile.save()
        new_client = APIClient()
        new_client.login(username="new_jacob", password="top_secret")
        create_mock_data("CIS-1920-201", TEST_SEMESTER)
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"id": ids["fifth_id"], "section": "CIS-1920-201"}),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)

    def test_registrations_multiple_users_autoresub(self):
        ids = self.create_auto_resubscribe_group()
        self.registrations_multiple_users_helper(ids, True)

    def test_registrations_put_resubscribe(self):
        self.create_auto_resubscribe_group(put=True)

    def test_put_invalid_id(self):
        response = self.client.put(
            reverse("registrations-detail", args=[100]),
            json.dumps({"deleted": True}),
            content_type="application/json",
        )
        self.assertEqual(404, response.status_code)

    def delete_and_resub_helper(self, auto_resub, put, delete_before_sim_webhook):
        """
        This function tests the desired functionality that you cannot resubscribe to
        a deleted registration, in a number of possible cases.  The parameter auto_resub
        specifies whether the test is run with auto resubscribe enabled or disabled,
        the put parameter specifies whether the test is run using PUT requests or POST requests
        to update, and delete_before_sim_webhook specifies whether the function should simulate
        the webhook and then delete, or delete before the webook triggers.
        """
        first_id = self.registration_cis1200.id
        if auto_resub:
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"auto_resubscribe": True}),
                    content_type="application/json",
                )
            else:
                self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "auto_resubscribe": True}),
                    content_type="application/json",
                )
        if not delete_before_sim_webhook:
            self.simulate_alert(self.cis1200, 1, should_send=True)
        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"deleted": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "deleted": True}),
                content_type="application/json",
            )
        self.assertEqual(200, response.status_code)
        if delete_before_sim_webhook:
            self.simulate_alert(self.cis1200, 1, should_send=False)
        if not auto_resub:
            if put:
                response = self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"resubscribe": True}),
                    content_type="application/json",
                )
            else:
                response = self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "resubscribe": True}),
                    content_type="application/json",
                )
            self.assertEqual(400, response.status_code)
            self.assertEqual(
                "You cannot resubscribe to a deleted registration.",
                response.data["detail"],
            )
        if not delete_before_sim_webhook:
            self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
            if auto_resub:
                self.assertFalse(
                    hasattr(
                        Registration.objects.get(id=first_id).resubscribed_to,
                        "resubscribed_to",
                    )
                )
                self.assertFalse(Registration.objects.get(id=first_id).deleted)
                self.assertIsNone(Registration.objects.get(id=first_id).deleted_at)
                self.assertTrue(Registration.objects.get(id=first_id).resubscribed_to.deleted)
                self.assertIsNotNone(
                    Registration.objects.get(id=first_id).resubscribed_to.deleted_at
                )
                self.assertFalse(
                    Registration.objects.get(id=first_id).resubscribed_to.notification_sent
                )
        else:
            self.assertFalse(Registration.objects.get(id=first_id).notification_sent)
            self.assertFalse(hasattr(Registration.objects.get(id=first_id), "resubscribed_to"))
            self.assertTrue(Registration.objects.get(id=first_id).deleted)
            self.assertIsNotNone(Registration.objects.get(id=first_id).deleted_at)

    @data(
        *(
            ({"delete_before_sim_webhook": x, "auto_resub": y, "put": z}, None)
            for x in (False, True)
            for y in (False, True)
            for z in (False, True)
        )
    )
    @unpack
    def test_delete_and_resub(self, value, result):
        self.delete_and_resub_helper(**value)

    def test_registrations_no_deleted(self):
        ids = self.create_auto_resubscribe_group()
        response = self.client.put(
            reverse("registrations-detail", args=[ids["fifth_id"]]),
            json.dumps({"deleted": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(0, len([r for r in response.data if str(r["id"]) == str(ids["fifth_id"])]))
        response = self.client.get(reverse("registrations-detail", args=[ids["fifth_id"]]))
        self.assertEqual(200, response.status_code)

    def test_cancel_resubscribe_current_group(self):
        ids = self.create_auto_resubscribe_group()
        response = self.client.put(
            reverse("registrations-detail", args=[ids["fifth_id"]]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        fifth_reg = Registration.objects.get(id=ids["fifth_id"])
        self.assertTrue(fifth_reg.cancelled)
        response = self.client.put(
            reverse("registrations-detail", args=[ids["fifth_id"]]),
            json.dumps({"resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        sixth_id = Registration.objects.get(id=ids["fifth_id"]).resubscribed_to.id
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        self.assertEqual(0, len([r for r in response.data if str(r["id"]) == str(ids["fifth_id"])]))
        self.assertEqual(1, len([r for r in response.data if str(r["id"]) == str(sixth_id)]))
        response = self.client.get(reverse("registrations-detail", args=[ids["fifth_id"]]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(sixth_id, response.data["id"])

    def test_cancel_send_alert(self):
        ids = self.create_auto_resubscribe_group()
        """
        Resubscribe chains created:
        first -> third -> fourth (CIS-1200-001)
        second (CIS-1600-001)
        fifth (CIS-1210-001)
        """
        response = self.client.put(
            reverse("registrations-detail", args=[ids["fourth_id"]]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)

        self.simulate_alert(self.cis1200, 4, close_notification=True, should_send=False)
        self.simulate_alert(self.cis1200, 5, should_send=False)

        response = self.client.put(
            reverse("registrations-detail", args=[ids["fourth_id"]]),
            json.dumps({"resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        sixth_id = response.data.get("id")

        response = self.client.put(
            reverse("registrations-detail", args=[sixth_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)

        response = self.client.put(
            reverse("registrations-detail", args=[sixth_id]),
            json.dumps({"resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        seventh_id = response.data.get("id")

        response = self.client.put(
            reverse("registrations-detail", args=[seventh_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)

        self.simulate_alert(self.cis1200, 6, close_notification=True, should_send=False)
        self.simulate_alert(self.cis1200, 7, should_send=False)

    def resub_after_new_registration_for_section(self, put):
        """
        This function tests that you cannot resubscribe to a registration if you have already
        made a new registration for the same section (using PUT or POST).
        """
        first_id = self.registration_cis1200.id
        self.simulate_alert(self.cis1200, 1, should_send=True)

        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        second_id = response.data.get("id")
        self.assertNotEquals(first_id, second_id)

        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"resubscribe": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "resubscribe": True}),
                content_type="application/json",
            )
        self.assertEqual(409, response.status_code)

    def test_resub_after_new_registration_for_section_put(self):
        self.resub_after_new_registration_for_section(put=True)

    def test_resub_after_new_registration_for_section_post(self):
        self.resub_after_new_registration_for_section(put=False)

    def test_registration_closed(self):
        self.create_resubscribe_group()
        Option.objects.update_or_create(key="REGISTRATION_OPEN", value_type="BOOL", value="FALSE")
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(503, response.status_code)

    def resub_when_registration_is_closed(self, put):
        """
        This function tests that you cannot resubscribe if registration is closed.
        """

        Option.objects.update_or_create(key="REGISTRATION_OPEN", value_type="BOOL", value="FALSE")

        first_id = self.registration_cis1200.id
        self.simulate_alert(self.cis1200, 1, should_send=True)

        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"resubscribe": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "resubscribe": True}),
                content_type="application/json",
            )
        self.assertEqual(503, response.status_code)

    def test_resub_when_registration_is_closed_put(self):
        self.resub_when_registration_is_closed(put=True)

    def test_resub_when_registration_is_closed_post(self):
        self.resub_when_registration_is_closed(put=False)

    def test_registration_after_adp(self):
        self.create_resubscribe_group()

        current_adp = get_add_drop_period(semester=TEST_SEMESTER)
        current_adp.end = datetime.utcnow().replace(tzinfo=gettz(TIME_ZONE)) - timedelta(days=1)
        current_adp.save()

        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1600-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(503, response.status_code)

    def resub_after_adp(self, put):
        """
        This function tests that you cannot resubscribe after the add/drop period ends.
        """

        first_id = self.registration_cis1200.id
        self.simulate_alert(self.cis1200, 1, should_send=True)

        current_adp = get_add_drop_period(semester=TEST_SEMESTER)
        current_adp.end = datetime.utcnow().replace(tzinfo=gettz(TIME_ZONE)) - timedelta(days=1)
        current_adp.save()

        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"resubscribe": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "resubscribe": True}),
                content_type="application/json",
            )
        self.assertEqual(503, response.status_code)

    def test_resub_after_adp_put(self):
        self.resub_after_adp(put=True)

    def test_resub_after_adp_post(self):
        self.resub_after_adp(put=False)

    def test_registration_list_multiple_candidates_same_section(self):
        """
        This function tests that registrations-list does not return multiple registrations
        for the same section.
        """

        ids = self.create_auto_resubscribe_group()

        """
        Resubscribe chains created:
        first -> third -> fourth (CIS-1200-001)
        second (CIS-1600-001)
        fifth (CIS-1210-001)
        """

        response = self.client.put(
            reverse("registrations-detail", args=[ids["first_id"]]),
            json.dumps({"auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)

        self.simulate_alert(self.cis1200, 4, close_notification=True, should_send=False)
        self.simulate_alert(self.cis1200, 5, should_send=True)

        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-1200-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        sixth_id = response.data.get("id")

        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        self.assertEqual(3, len(set(item.get("id") for item in response.data)))
        self.assertEqual(1, len([item for item in response.data if item.get("id") == sixth_id]))
        self.assertEqual(
            1,
            len([item for item in response.data if item.get("id") == ids["second_id"]]),
        )
        self.assertEqual(
            1,
            len([item for item in response.data if item.get("id") == ids["fifth_id"]]),
        )

    def cancel_and_resub_helper(self, auto_resub, put, cancel_before_sim_webhook):
        """
        This function tests that you can resubscribe to a cancelled alert, in multiple possible
        cases.  The auto_resub parameter specifies whether or not the auto resubscribe should be
        enabled, the put paraeter specifies whether the update request should be PUT or POST,
        and the cancel_before_sim_webhook paramater specifies whether or not the function should
        cancel the registration before or after the webhook triggers.
        """
        first_id = self.registration_cis1200.id
        if auto_resub:
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"auto_resubscribe": True}),
                    content_type="application/json",
                )
            else:
                self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "auto_resubscribe": True}),
                    content_type="application/json",
                )
        if not cancel_before_sim_webhook:
            self.simulate_alert(self.cis1200, 1, should_send=True)
        if put:
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"cancelled": True}),
                content_type="application/json",
            )
        else:
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "cancelled": True}),
                content_type="application/json",
            )
        if not cancel_before_sim_webhook and not auto_resub:
            self.assertEqual(400, response.status_code)
            self.assertEqual("You cannot cancel a sent registration.", response.data["detail"])
        else:
            self.assertEqual(200, response.status_code)
            self.assertEqual("Registration cancelled", response.data["detail"])
        if cancel_before_sim_webhook:
            self.simulate_alert(self.cis1200, 1, should_send=False)
        if not auto_resub:
            if put:
                response = self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"resubscribe": True}),
                    content_type="application/json",
                )
            else:
                response = self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "resubscribe": True}),
                    content_type="application/json",
                )
            self.assertEqual(200, response.status_code)
            self.assertEqual("Resubscribed successfully", response.data["detail"])
        if not cancel_before_sim_webhook:
            self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
            if auto_resub:
                self.assertFalse(
                    hasattr(
                        Registration.objects.get(id=first_id).resubscribed_to,
                        "resubscribed_to",
                    )
                )
                self.assertFalse(Registration.objects.get(id=first_id).cancelled)
                self.assertIsNone(Registration.objects.get(id=first_id).cancelled_at)
                self.assertTrue(Registration.objects.get(id=first_id).resubscribed_to.cancelled)
                self.assertIsNotNone(
                    Registration.objects.get(id=first_id).resubscribed_to.cancelled_at
                )
                self.assertFalse(
                    Registration.objects.get(id=first_id).resubscribed_to.notification_sent
                )
        else:
            self.assertFalse(Registration.objects.get(id=first_id).notification_sent)
            self.assertEquals(
                not auto_resub or not cancel_before_sim_webhook,
                hasattr(Registration.objects.get(id=first_id), "resubscribed_to"),
            )
            if not auto_resub or not cancel_before_sim_webhook:
                self.assertTrue(Registration.objects.get(id=first_id).resubscribed_to.is_active)
                self.assertFalse(
                    Registration.objects.get(id=first_id).resubscribed_to.notification_sent
                )
            self.assertTrue(Registration.objects.get(id=first_id).cancelled)
            self.assertIsNotNone(Registration.objects.get(id=first_id).cancelled_at)

    @data(
        *(
            ({"cancel_before_sim_webhook": x, "auto_resub": y, "put": z}, None)
            for x in (False, True)
            for y in (False, True)
            for z in (False, True)
        )
    )
    @unpack
    def test_cancel_and_resub(self, value, result):
        self.cancel_and_resub_helper(**value)

    def test_cancel_deleted(self):
        first_id = self.registration_cis1200.id
        self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"deleted": True}),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEquals(400, response.status_code)
        self.assertEquals("You cannot cancel a deleted registration.", response.data["detail"])

    def test_cancel_sent(self):
        first_id = self.registration_cis1200.id
        self.simulate_alert(self.cis1200, 1, should_send=True)
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEquals(400, response.status_code)
        self.assertEquals("You cannot cancel a sent registration.", response.data["detail"])

    def test_delete_cancelled(self):
        first_id = self.registration_cis1200.id
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEquals(200, response.status_code)
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"deleted": True}),
            content_type="application/json",
        )
        self.assertEquals(200, response.status_code)

    def test_registrations_contain_cancelled(self):
        ids = self.create_auto_resubscribe_group()
        response = self.client.put(
            reverse("registrations-detail", args=[ids["fifth_id"]]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        self.assertEqual(1, len([r for r in response.data if str(r["id"]) == str(ids["fifth_id"])]))
        response = self.client.get(reverse("registrations-detail", args=[ids["fifth_id"]]))
        self.assertEqual(200, response.status_code)

    def changeattrs_update_order_helper(self, put, update_field):
        """
        This function tests changing attributes of a registration, and checks that the proper
        order of priorities is satisfied, in multiple possible cases.  The put parameter
        specifies whether to send the update as a PUT or POST request, while the update_field
        parameter specifies which dominant field to update ("resub" or "deleted").
        """
        first_id = self.registration_cis1200.id
        if update_field == "resub":
            self.simulate_alert(self.cis1200, 1)
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps(
                        {
                            "resubscribe": True,
                            "deleted": True,
                            "auto_resubscribe": True,
                            "close_notification": True,
                        }
                    ),
                    content_type="application/json",
                )
            else:
                self.client.post(
                    reverse("registrations-list"),
                    json.dumps(
                        {
                            "id": first_id,
                            "resubscribe": True,
                            "deleted": True,
                            "auto_resubscribe": True,
                            "close_notification": True,
                        }
                    ),
                    content_type="application/json",
                )
            self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
            self.assertFalse(
                Registration.objects.get(id=first_id).resubscribed_to.notification_sent
            )
            self.assertFalse(Registration.objects.get(id=first_id).deleted)
            self.assertIsNone(Registration.objects.get(id=first_id).deleted_at)
            self.assertFalse(Registration.objects.get(id=first_id).resubscribed_to.deleted)
            self.assertIsNone(Registration.objects.get(id=first_id).resubscribed_to.deleted_at)
            self.assertFalse(Registration.objects.get(id=first_id).auto_resubscribe)
            self.assertFalse(Registration.objects.get(id=first_id).close_notification)
            self.assertFalse(Registration.objects.get(id=first_id).resubscribed_to.auto_resubscribe)
        if update_field == "deleted":
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps(
                        {
                            "deleted": True,
                            "auto_resubscribe": True,
                            "close_notification": True,
                        }
                    ),
                    content_type="application/json",
                )
            else:
                self.client.post(
                    reverse("registrations-list"),
                    json.dumps(
                        {
                            "id": first_id,
                            "deleted": True,
                            "auto_resubscribe": True,
                            "close_notification": True,
                        }
                    ),
                    content_type="application/json",
                )
            self.assertTrue(Registration.objects.get(id=first_id).deleted)
            self.assertIsNotNone(Registration.objects.get(id=first_id).deleted_at)
            self.assertFalse(Registration.objects.get(id=first_id).auto_resubscribe)
            self.assertFalse(Registration.objects.get(id=first_id).close_notification)

    @data(*(((b, v), None) for b in (True, False) for v in ("resub", "deleted")))
    @unpack
    def test_changeattrs_update_order(self, value, result):
        self.changeattrs_update_order_helper(*value)

    def close_notification_creation_helper(self, push_notif):
        """
        This helper tests the creation of a registration with close notifications enabled, in two
        possible cases; with push notifications enabled (push_notif parameter set to True),
        or disabled (push_notif set to False).
        """
        contact_infos = [{"number": "+19178286431", "email": "j@gmail.com", "push_username": None}]
        if push_notif:
            response = self.client.put(
                reverse("user-view"),
                json.dumps(
                    {
                        "profile": {
                            "email": self.user.profile.email,
                            "phone": self.user.profile.phone,
                            "push_notifications": True,
                        }
                    }
                ),
                content_type="application/json",
            )
            self.assertEquals(200, response.status_code)
            contact_infos[0]["push_username"] = self.user.username
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps(
                {
                    "section": "CIS-1600-001",
                    "auto_resubscribe": True,
                    "close_notification": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        first_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[first_id]))
        self.assertEqual(response.status_code, 200)
        r = Registration.objects.get(id=first_id)
        self.check_model_with_response_data(r, response.data)
        self.assertTrue(r.close_notification)
        self.assertTrue(r.auto_resubscribe)
        self.assertTrue(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        self.simulate_alert(
            self.cis1600,
            1,
            close_notification=True,
            should_send=False,
            contact_infos=contact_infos,
        )
        r = Registration.objects.get(id=first_id)
        self.assertTrue(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        self.simulate_alert(self.cis1600, 2, should_send=True, contact_infos=contact_infos)
        r = Registration.objects.get(id=first_id)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertTrue(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )
        contact_infos[0]["number"] = None
        self.simulate_alert(
            self.cis1600,
            3,
            close_notification=True,
            should_send=True,
            contact_infos=contact_infos,
        )
        r = Registration.objects.get(id=first_id)
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="O")
        )
        self.assertFalse(
            r in get_registrations_for_alerts("CIS-1600-001", TEST_SEMESTER, course_status="C")
        )

    def test_close_notification_creation(self):
        self.close_notification_creation_helper(False)

    def test_close_notification_creation_helper_push(self):
        self.close_notification_creation_helper(True)

    def test_close_notification_create_only_text(self):
        self.user.profile.push_notifications = False
        self.user.profile.email = None
        self.user.profile.save()
        self.user.save()
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps(
                {
                    "section": "CIS-1600-001",
                    "auto_resubscribe": True,
                    "close_notification": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 406)
        self.assertEqual(1, Registration.objects.count())

    def close_notification_update_helper(self, put, auto_resub):
        """
        This helper tests the updating of a registration with close notifications enabled, in
        multiple possible cases.  The put parameter specifies whether to send the update via a
        PUT or POST request, and the auto_resub parameter specifies whether the enable or disable
        auto resubscription on the registration.
        """
        first_id = self.registration_cis1200.id
        if put:
            self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"auto_resubscribe": auto_resub, "close_notification": True}),
                content_type="application/json",
            )
        else:
            self.client.post(
                reverse("registrations-list"),
                json.dumps(
                    {
                        "id": first_id,
                        "auto_resubscribe": auto_resub,
                        "close_notification": True,
                    }
                ),
                content_type="application/json",
            )
        r = Registration.objects.get(id=first_id)
        self.assertEquals(auto_resub, r.auto_resubscribe)
        self.assertTrue(r.close_notification)

    @data(*(((put, auto_resub), None) for put in [True, False] for auto_resub in [True, False]))
    @unpack
    def test_close_notification_update(self, value, result):
        self.close_notification_update_helper(*value)

    def test_close_notification_update_only_text(self):
        self.user.profile.push_notifications = False
        self.user.profile.email = None
        self.user.profile.save()
        self.user.save()
        first_id = self.registration_cis1200.id
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"auto_resubscribe": True, "close_notification": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 406)
        self.assertEqual(1, Registration.objects.count())

    def close_notification_cancel_helper(self, delete=False):
        """
        Ensure that cancelling or deleting a registration also cancels a pending close notification
        """
        contact_infos = [
            {
                "number": "+19178286431",
                "email": "j@gmail.com",
                "push_username": self.user.username,
            }
        ]
        first_id = self.registration_cis1200.id

        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"auto_resubscribe": True, "close_notification": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        self.simulate_alert(self.cis1200, 1, should_send=True)

        second_id = self.registration_cis1200.resubscribed_to.id

        response = self.client.put(
            reverse("registrations-detail", args=[second_id]),
            json.dumps({("deleted" if delete else "cancelled"): True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        first_reg = Registration.objects.get(id=second_id)

        if delete:
            self.assertTrue(first_reg.deleted)
        else:
            self.assertTrue(first_reg.cancelled)

        self.simulate_alert(
            self.cis1200,
            2,
            close_notification=True,
            should_send=False,
            contact_infos=contact_infos,
        )

    def test_close_notification_cancel(self):
        self.close_notification_cancel_helper(delete=False)

    def test_close_notification_delete(self):
        self.close_notification_cancel_helper(delete=True)

    def close_notification_resub_helper(self, put, auto_resub):
        """
        This function tests that resubscription properly carries over the close notification
        setting, in a number of possible cases.  The put parameter specifies whether to send the
        resubscribe request in a PUT or POST request, and the auto_resub parameter specifies
        whether to enable or disable auto resubscription on the registration.
        """
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps(
                {
                    "section": "CIS-1600-001",
                    "auto_resubscribe": auto_resub,
                    "close_notification": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        first_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[first_id]))
        self.assertEqual(response.status_code, 200)
        r = Registration.objects.get(id=first_id)
        self.check_model_with_response_data(r, response.data)
        self.assertTrue(r.close_notification)
        self.assertEquals(auto_resub, r.auto_resubscribe)
        response = self.client.get(reverse("registrations-detail", args=[first_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["close_notification"])
        self.assertEquals(auto_resub, response.data["auto_resubscribe"])
        self.simulate_alert(self.cis1600, 1, should_send=True)
        if not auto_resub:
            if put:
                response = self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"resubscribe": True}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
            else:
                response = self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "resubscribe": True}),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("registrations-detail", args=[first_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["close_notification"])
        self.assertEquals(auto_resub, response.data["auto_resubscribe"])

    @data(*(((put, auto_resub), None) for put in [True, False] for auto_resub in [True, False]))
    @unpack
    def test_close_notification_resub(self, value, result):
        self.close_notification_resub_helper(*value)

    def resub_attrs_maintained_helper(self, put):
        """
        This function checks that auto resubscribing carries over the auto_resubscribe property,
        for both PUT requests and POST requests.
        """
        first_id = self.registration_cis1200.id
        if put:
            self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"auto_resubscribe": True}),
                content_type="application/json",
            )
        else:
            self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "auto_resubscribe": True}),
                content_type="application/json",
            )
        self.simulate_alert(self.cis1200, 1)
        self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
        self.assertFalse(Registration.objects.get(id=first_id).resubscribed_to.notification_sent)
        self.assertTrue(Registration.objects.get(id=first_id).auto_resubscribe)
        self.assertTrue(Registration.objects.get(id=first_id).resubscribed_to.auto_resubscribe)

    @data((True, None), (False, None))
    @unpack
    def test_resub_attrs_maintained(self, value, result):
        self.resub_attrs_maintained_helper(value)

    def delete_and_change_attrs_helper(self, put):
        """
        This function tests that attributes are not changed if a registration is deleted in a
        PUT or POST update request.
        """
        first_id = self.registration_cis1200.id
        if put:
            self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"deleted": True}),
                content_type="application/json",
            )
            response = self.client.put(
                reverse("registrations-detail", args=[first_id]),
                json.dumps({"auto_resubscribe": True}),
                content_type="application/json",
            )
        else:
            self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "deleted": True}),
                content_type="application/json",
            )
            response = self.client.post(
                reverse("registrations-list"),
                json.dumps({"id": first_id, "auto_resubscribe": True}),
                content_type="application/json",
            )
        self.assertTrue(Registration.objects.get(id=first_id).deleted)
        self.assertIsNotNone(Registration.objects.get(id=first_id).deleted_at)
        self.assertFalse(Registration.objects.get(id=first_id).auto_resubscribe)
        self.assertEquals(400, response.status_code)
        self.assertEquals(
            "You cannot make changes to a deleted registration.",
            response.data["detail"],
        )

    @data((True, None), (False, None))
    @unpack
    def test_delete_and_change_attrs(self, value, result):
        self.delete_and_change_attrs_helper(value)

    def test_get_most_current(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["first_id"]).get_most_current(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_most_current(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["third_id"]).get_most_current(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_most_current(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_most_current(),
        )

    def test_get_most_current_iter(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["first_id"]).get_most_current_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_most_current_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["third_id"]).get_most_current_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_most_current_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_most_current_iter(),
        )

    def test_get_original_registration(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["first_id"]).get_original_registration(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_original_registration(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["third_id"]).get_original_registration(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_original_registration(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_original_registration(),
        )

    def test_get_original_registration_iter(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["first_id"]).get_original_registration_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_original_registration_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["third_id"]).get_original_registration_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_original_registration_iter(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_original_registration_iter(),
        )

    def test_get_resubscribe_group(self):
        ids = self.create_resubscribe_group()
        first = Registration.objects.get(id=ids["first_id"])
        third = Registration.objects.get(id=ids["third_id"])
        fourth = Registration.objects.get(id=ids["third_id"])
        self.assertEqual(len(first.get_resubscribe_group()), 3)
        self.assertEqual(len(third.get_resubscribe_group()), 3)
        self.assertEqual(len(fourth.get_resubscribe_group()), 3)
        self.assertTrue(first in third.get_resubscribe_group())
        self.assertTrue(third in first.get_resubscribe_group())
        self.assertTrue(first in fourth.get_resubscribe_group())
        self.assertTrue(fourth in first.get_resubscribe_group())
        self.assertTrue(third in fourth.get_resubscribe_group())
        self.assertTrue(fourth in third.get_resubscribe_group())

    def test_last_notification_sent_at(self):
        """
        This function checks that the last_notification_sent property is correct in data returned
        by registrations-list, registrationhistory-list, and registrations-detail
        """

        ids = self.create_auto_resubscribe_group()
        """
        Resubscribe chains created:
        first -> third -> fourth (CIS-1200-001)
        second (CIS-1600-001)
        fifth (CIS-1210-001)
        """

        # First check registrations-list
        response = self.client.get(reverse("registrations-list"))
        obs = dict()
        last_notification_sent_at_vals = dict()
        for specific_ids in ["second", "fourth", "fifth"]:
            ob_lst = [ob for ob in response.data if ob.get("id") == ids[specific_ids + "_id"]]
            self.assertEquals(1, len(ob_lst))
            obs[specific_ids] = ob_lst[0]
            last_notification_sent_at_vals[specific_ids] = ob_lst[0].get(
                "last_notification_sent_at"
            )
        self.assertIsNone(last_notification_sent_at_vals["second"])
        self.assertIsNotNone(last_notification_sent_at_vals["fourth"])
        self.assertIsNone(last_notification_sent_at_vals["fifth"])

        # Now check registration history
        response = self.client.get(reverse("registrationhistory-list"))
        for specific_ids in ["first", "third", "fourth"]:
            ob_lst = [ob for ob in response.data if ob.get("id") == ids[specific_ids + "_id"]]
            self.assertEquals(1, len(ob_lst))
            self.assertEquals(
                last_notification_sent_at_vals["fourth"],
                ob_lst[0].get("last_notification_sent_at"),
            )
        for specific_ids in ["second", "fifth"]:
            ob_lst = [ob for ob in response.data if ob.get("id") == ids[specific_ids + "_id"]]
            self.assertEquals(1, len(ob_lst))
            self.assertIsNone(ob_lst[0].get("last_notification_sent_at"))

        # Now check registration detail
        for specific_ids in ["first", "third", "fourth"]:
            response = self.client.get(
                reverse("registrations-detail", args=[ids[specific_ids + "_id"]])
            )
            self.assertEquals(
                last_notification_sent_at_vals["fourth"],
                response.data.get("last_notification_sent_at"),
            )
        for specific_ids in ["second", "fifth"]:
            response = self.client.get(
                reverse("registrations-detail", args=[ids[specific_ids + "_id"]])
            )
            self.assertIsNone(response.data.get("last_notification_sent_at"))


class TestAlertMeetingString(TestCase):
    def setUp(self):
        set_semester()
        user = User.objects.create_user(username="jacob", password="top_secret")
        user.save()
        self.user = user

    def create_reg(self, full_code, **kwargs):
        _, section, _, _ = get_or_create_course_and_section(full_code, TEST_SEMESTER)
        reg = Registration(section=section, user=self.user, **kwargs)
        reg.save()
        return reg

    def test_json_list_is_parsed_correctly(self):
        reg = self.create_reg(full_code="CIS-1200-001")
        reg.section.meeting_times = '["MW 1:45 PM - 3:14 PM", "T 1:45 PM - 2:44 PM"]'
        expected = "MW 1:45 PM - 3:14 PM, T 1:45 PM - 2:44 PM"
        self.assertEquals(expected, get_meeting_string(reg))

    def test_empty_string_returns_empty_string(self):
        reg = self.create_reg(full_code="CIS-1200-001")
        reg.section.meeting_times = ""
        expected = ""
        self.assertEquals(expected, get_meeting_string(reg))

    def test_invalid_json_returns_empty_string(self):
        reg = self.create_reg(full_code="CIS-1200-001")
        reg.section.meeting_times = "MW 1:45 PM - 3:14 PM, T 1:45 PM - 2:44 PM"
        expected = ""
        self.assertEquals(expected, get_meeting_string(reg))
