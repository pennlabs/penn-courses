import base64
import importlib
import json
from unittest.mock import patch

from ddt import data, ddt, unpack
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from options.models import Option
from rest_framework.test import APIClient
from tests.courses.util import create_mock_data

from alert import tasks
from alert.models import SOURCE_PCA, Registration, RegStatus, register_for_course
from courses.models import StatusUpdate
from courses.util import get_or_create_course_and_section


TEST_SEMESTER = "2019A"


def contains_all(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()


def override_delay(modules_names, before_func, before_kwargs):
    """
    A function that makes delay()ed functions synchronous for testing.  Please read the full docs
    (RTFM) before using to prevent unintended behavior or errors.
    See AlertRegistrationTestCase.simulate_alert for an example of how to use this function

    Args:
        modules_names: a list of 2-tuples of the form (module, name) where module is the module in
            which the delay()ed function is located and name is its name.  Note that each 2-tuple
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
        before_func: a function (not its name, the actual function as a variable) which will be
            executed to trigger the first delay()ed function in modules_names.
            Note that this function MUST trigger the first delay()ed function in modules_names
            or an error will be thrown.
            Example of a valid before_func argument (from AlertRegistrationTestCase.simulate_alert):
                a function simulating the webhook firing which causes send_course_alerts.delay()
                to be called
        before_kwargs: a dictionary of keyword-value arguments which will be
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


@patch("alert.models.Text.send_alert")
@patch("alert.models.Email.send_alert")
class SendAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        course, section, _, _ = get_or_create_course_and_section("CIS-160-001", TEST_SEMESTER)
        self.r = Registration(email="yo@example.com", phone="+15555555555", section=section)

        self.r.save()

    def test_send_alert(self, mock_email, mock_text):
        self.assertFalse(Registration.objects.get(id=self.r.id).notification_sent)
        tasks.send_alert(self.r.id, sent_by="ADM")
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)
        self.assertTrue(Registration.objects.get(id=self.r.id).notification_sent)
        self.assertEqual("ADM", Registration.objects.get(id=self.r.id).notification_sent_by)

    def test_dont_resend_alert(self, mock_email, mock_text):
        self.r.notification_sent = True
        self.r.save()
        tasks.send_alert(self.r.id)
        self.assertFalse(mock_email.called)
        self.assertFalse(mock_text.called)

    def test_resend_alert_forced(self, mock_email, mock_text):
        self.r.notification_sent = True
        self.r.save()
        self.r.alert(True)
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)


class RegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.sections = []
        self.sections.append(get_or_create_course_and_section("CIS-160-001", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-160-002", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)[1])

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
        res, norm, _ = register_for_course("cis160001", "e@example.com", "+15555555555")
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual("CIS-160-001", norm)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual("CIS-160-001", r.section.full_code)

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


class ResubscribeTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section, _, _ = get_or_create_course_and_section("CIS-160-001", TEST_SEMESTER)
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

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result, reg3)


class WebhookTriggeredAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section, _, _ = get_or_create_course_and_section("CIS-160-001", TEST_SEMESTER)
        self.r1 = Registration(email="e@example.com", phone="+15555555555", section=self.section)
        self.r2 = Registration(email="f@example.com", phone="+15555555556", section=self.section)
        self.r3 = Registration(email="g@example.com", phone="+15555555557", section=self.section)
        self.r1.save()
        self.r2.save()
        self.r3.save()

    def test_collect_all(self):
        result = tasks.get_active_registrations(self.section.full_code, TEST_SEMESTER)
        expected_ids = [r.id for r in [self.r1, self.r2, self.r3]]
        result_ids = [r.id for r in result]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)

        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_none(self):
        get_or_create_course_and_section("CIS-121-001", TEST_SEMESTER)
        result = tasks.get_active_registrations("CIS-121-001", TEST_SEMESTER)
        self.assertTrue(len(result) == 0)

    def test_collect_one(self):
        self.r2.notification_sent = True
        self.r3.notification_sent = True
        self.r2.save()
        self.r3.save()
        result_ids = [
            r.id for r in tasks.get_active_registrations(self.section.full_code, TEST_SEMESTER)
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
            r.id for r in tasks.get_active_registrations(self.section.full_code, TEST_SEMESTER)
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
            "course_section": "ANTH361401",
            "previous_status": "X",
            "status": "O",
            "status_code_normalized": "Open",
            "term": TEST_SEMESTER,
        }
        Option.objects.update_or_create(
            key="SEND_FROM_WEBHOOK", value_type="BOOL", defaults={"value": "TRUE"}
        )
        Option.objects.update_or_create(
            key="SEMESTER", value_type="TXT", defaults={"value": TEST_SEMESTER}
        )

    def test_alert_called_and_sent_intl(self, mock_alert):
        res = self.client.post(
            reverse("webhook", urlconf="alert.urls"),
            data=json.dumps(
                {
                    "course_section": "INTLBUL001",
                    "previous_status": "X",
                    "status": "O",
                    "status_code_normalized": "Open",
                    "term": TEST_SEMESTER,
                }
            ),
            content_type="application/json",
            **self.headers,
        )

        self.assertEqual(200, res.status_code)
        self.assertTrue(mock_alert.called)
        self.assertEqual("INTLBUL001", mock_alert.call_args[0][0])
        self.assertEqual("2019A", mock_alert.call_args[1]["semester"])
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
        self.assertEqual("ANTH361401", mock_alert.call_args[0][0])
        self.assertEqual("2019A", mock_alert.call_args[1]["semester"])
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
        self.assertFalse("sent" in json.loads(res.content)["message"])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

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
                    "course_section": "ANTH361401",
                    "previous_status": "X",
                    "status_code_normalized": "Open",
                    "term": "2019A",
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
        self.assertEqual(401, res.status_code)
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
        self.assertEqual(401, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())


class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, cis120_section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        _, cis160_section = create_mock_data("CIS-160-001", TEST_SEMESTER)
        self.statusUpdates = [
            StatusUpdate(section=cis120_section, old_status="O", new_status="C", alert_sent=False),
            StatusUpdate(section=cis120_section, old_status="C", new_status="O", alert_sent=True),
            StatusUpdate(section=cis160_section, old_status="C", new_status="O", alert_sent=True),
        ]
        for s in self.statusUpdates:
            s.save()
        self.client = APIClient()

    def test_cis120(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-120-001"]))
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

    def test_cis160(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-160-001"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["old_status"], "C")
        self.assertEqual(response.data[0]["new_status"], "O")
        self.assertEqual(response.data[0]["alert_sent"], True)
        self.assertFalse(hasattr(response.data[0], "request_body"))

    def test_cis121_missing(self):
        response = self.client.get(reverse("statusupdate", args=["CIS-121"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


class UserDetailTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="jacob", password="top_secret")
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")

    def test_settings_before_create(self):
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])

    def test_update_settings(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example@email.com", "phone": "3131234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_update_settings_change_first_name(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "first_name": "newname",
                    "last_name": "",
                    "profile": {"email": "example@email.com", "phone": "3131234567"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "newname")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "newname")
        self.assertEqual(response.data["last_name"], "")

    def test_update_settings_change_last_name(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "first_name": "",
                    "last_name": "newname",
                    "profile": {"email": "example@email.com", "phone": "3131234567"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "newname")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "newname")

    def test_update_settings_change_username(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "username": "newusername",
                    "first_name": "",
                    "last_name": "",
                    "profile": {"email": "example@email.com", "phone": "3131234567"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_add_fields(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "first_name": "",
                    "last_name": "",
                    "middle_name": "m",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "favorite_color": "blue",
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse("favorite_color" in response.data["profile"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertFalse("middle_name" in response.data)
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse("favorite_color" in response.data["profile"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertFalse("middle_name" in response.data)

    def test_ignore_fields_email_update(self):
        self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "first_name": "fname",
                    "last_name": "lname",
                    "profile": {"email": "example@email.com", "phone": "3131234567"},
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example2@email.com"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")

    def test_ignore_fields_phone_update(self):
        self.client.put(
            reverse("user-profile"),
            json.dumps(
                {
                    "first_name": "fname",
                    "last_name": "lname",
                    "profile": {"email": "example@email.com", "phone": "3131234567"},
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"phone": "2121234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")

    def test_invalid_phone(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example@email.com", "phone": "abc"}}),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])

    def test_invalid_email(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example@", "phone": "3131234567"}}),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])

    def test_null_email(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": None, "phone": "3131234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_null_phone(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example@email.com", "phone": None}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_both_null(self):
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": None, "phone": None}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_multiple_users_independent(self):
        User.objects.create_user(username="murey", password="top_secret")
        client2 = APIClient()
        client2.login(username="murey", password="top_secret")
        response = self.client.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example@email.com", "phone": "3131234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = client2.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example2@email.com", "phone": "2121234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["username"], "murey")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = client2.get(reverse("user-profile"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["username"], "murey")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_user_not_logged_in(self):
        client2 = APIClient()
        response = client2.put(
            reverse("user-profile"),
            json.dumps({"profile": {"email": "example2@email.com", "phone": "2121234567"}}),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)
        response = client2.get(reverse("user-profile"))
        self.assertEqual(403, response.status_code)


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
        self.user.profile.phone = "+11234567890"
        self.user.profile.save()
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")
        _, self.cis120 = create_mock_data("CIS-120-001", TEST_SEMESTER)
        _, self.cis160 = create_mock_data("CIS-160-001", TEST_SEMESTER)
        _, self.cis121 = create_mock_data("CIS-121-001", TEST_SEMESTER)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-120-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        self.registration_cis120 = Registration.objects.get(section=self.cis120)

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
        self.assertEqual(model.created_at, self.convert_date(data["created_at"]))
        self.assertEqual(model.updated_at, self.convert_date(data["updated_at"]))

    def simulate_alert_helper_before(self, section):
        auth = base64.standard_b64encode("webhook:password".encode("ascii"))
        headers = {
            "Authorization": f"Basic {auth.decode()}",
        }
        body = {
            "course_section": section.full_code.replace("-", ""),
            "previous_status": "X",
            "status": "O",
            "status_code_normalized": "Open",
            "term": section.semester,
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
        self, section, num_status_updates=None, contact_infos=None, should_send=True
    ):
        contact_infos = (
            [{"number": "+11234567890", "email": "j@gmail.com"}]
            if contact_infos is None
            else contact_infos
        )
        with patch("alert.alerts.send_email", return_value=True) as send_email_mock:
            with patch("alert.alerts.send_text", return_value=True) as send_text_mock:
                override_delay(
                    [("alert.tasks", "send_course_alerts"), ("alert.tasks", "send_alert"),],
                    self.simulate_alert_helper_before,
                    {"section": section},
                )
                self.assertEqual(
                    0 if not should_send else len(contact_infos), send_email_mock.call_count,
                )
                self.assertEqual(
                    0 if not should_send else len(contact_infos), send_text_mock.call_count,
                )
                for c in contact_infos:
                    self.assertEqual(
                        0 if not should_send else 1,
                        len([m for m in send_text_mock.call_args_list if m[0][0] == c["number"]]),
                    )
                    self.assertEqual(
                        0 if not should_send else 1,
                        len(
                            [m for m in send_email_mock.call_args_list if m[1]["to"] == c["email"]]
                        ),
                    )
                for r in Registration.objects.filter(section=section):
                    if hasattr(r, "resubscribed_to"):
                        self.assertEquals(should_send, r.notification_sent)
                        if should_send:
                            self.assertIsNotNone(r.notification_sent_at)
                        else:
                            self.assertNone(r.notification_sent_at)
                if num_status_updates is not None:
                    self.assertEqual(num_status_updates, StatusUpdate.objects.count())
                for u in StatusUpdate.objects.all():
                    self.assertTrue(u.alert_sent)

    def create_resubscribe_group(self):
        first_id = self.registration_cis120.id
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-160-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        second_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[second_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=second_id), response.data)
        self.simulate_alert(self.cis120, 1)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"id": first_id, "resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        third_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(self.registration_cis120.resubscribed_to, response.data)
        self.simulate_alert(self.cis120, 2)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"id": third_id, "resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        fourth_id = response.data["id"]
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-121-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        fifth_id = response.data["id"]
        # first is original CIS120 registration, second is disconnected CIS160 registration,
        # third is resubscribed from first, fourth is resubscribed from third,
        # and fifth is disconnected CIS121 registration
        return {
            "first_id": first_id,
            "second_id": second_id,
            "third_id": third_id,
            "fourth_id": fourth_id,
            "fifth_id": fifth_id,
        }

    def create_auto_resubscribe_group(self, put=False):
        first_id = self.registration_cis120.id
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
            json.dumps({"section": "CIS-160-001", "auto_resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        second_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[second_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=second_id), response.data)
        self.simulate_alert(self.cis120, 1)
        first_ob = Registration.objects.get(id=first_id)
        third_ob = first_ob.resubscribed_to
        third_id = third_ob.id
        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(third_ob, response.data)
        response = self.client.get(reverse("registrations-detail", args=[third_id]))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(third_ob, response.data)
        self.simulate_alert(self.cis120, 2)
        first_ob = Registration.objects.get(id=first_id)
        third_ob = first_ob.resubscribed_to
        fourth_ob = third_ob.resubscribed_to
        fourth_id = fourth_ob.id
        response = self.client.get(reverse("registrations-detail", args=[fourth_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(fourth_ob, response.data)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-121-001", "auto_resubscribe": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        fifth_id = response.data["id"]
        response = self.client.get(reverse("registrations-detail", args=[fifth_id]))
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=fifth_id), response.data)
        # first is original CIS120 registration, second is disconnected CIS160 registration,
        # third is auto-resubscribed from first, fourth is auto-resubscribed from third,
        # and fifth is disconnected CIS121 registration
        return {
            "first_id": first_id,
            "second_id": second_id,
            "third_id": third_id,
            "fourth_id": fourth_id,
            "fifth_id": fifth_id,
        }

    def test_registrations_get_simple(self):
        response = self.client.get(
            reverse("registrations-detail", args=[self.registration_cis120.pk])
        )
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(self.registration_cis120, response.data)

    def test_semester_not_set(self):
        Option.objects.filter(key="SEMESTER").delete()
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(500, response.status_code)
        self.assertTrue("SEMESTER" in response.data["detail"])

    def test_registrations_get_only_current_semester(self):
        _, self.cis110in2019C = create_mock_data("CIS-110-001", "2019C")
        registration = Registration(section=self.cis110in2019C, user=self.user, source="PCA")
        registration.auto_resubscribe = False
        registration.save()
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(
            Registration.objects.get(section=self.cis120), response.data[0]
        )

    def test_registration_history_get_only_current_semester(self):
        _, self.cis110in2019C = create_mock_data("CIS-110-001", "2019C")
        registration = Registration(section=self.cis110in2019C, user=self.user, source="PCA")
        registration.auto_resubscribe = False
        registration.save()
        response = self.client.get(reverse("registrationhistory-list"))
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(
            Registration.objects.get(section=self.cis120), response.data[0]
        )

    def registrations_resubscribe_get_old_and_history_helper(self, ids):
        response = self.client.get(reverse("registrations-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        fourth_data = next(item for item in response.data if item["id"] == ids["fourth_id"])
        second_data = next(item for item in response.data if item["id"] == ids["second_id"])
        fifth_data = next(item for item in response.data if item["id"] == ids["fifth_id"])
        self.check_model_with_response_data(
            self.registration_cis120.resubscribed_to.resubscribed_to, fourth_data
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
            self.registration_cis120.resubscribed_to, Registration.objects.get(id=ids["third_id"]),
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
        first_ob = Registration.objects.get(id=ids["first_id"])
        fourth_ob = Registration.objects.get(id=ids["fourth_id"])
        self.simulate_alert(self.cis120, 3)
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
            json.dumps({"section": "CIS-160-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(409, response.status_code)
        response = self.client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-120-001", "auto_resubscribe": False}),
            content_type="application/json",
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual(num, Registration.objects.count())

    def registrations_multiple_users_helper(self, ids, auto_resub=False):
        new_user = User.objects.create_user(username="new_jacob", password="top_secret")
        new_user.save()
        new_user.profile.email = "newj@gmail.com"
        new_user.profile.phone = "+12234567890"
        new_user.profile.save()
        new_client = APIClient()
        new_client.login(username="new_jacob", password="top_secret")
        create_mock_data("CIS-192-201", TEST_SEMESTER)
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-192-201", "auto_resubscribe": auto_resub}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        new_first_id = response.data["id"]
        response = new_client.post(
            reverse("registrations-list"),
            json.dumps({"section": "CIS-120-001", "auto_resubscribe": auto_resub}),
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
            0, len([item for item in response.data if item["id"] in [id for id in ids.values()]]),
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
        self.simulate_alert(
            self.cis120,
            3,
            [
                {"number": "+11234567890", "email": "j@gmail.com"},
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
            0, len([item for item in response.data if item["id"] in [id for id in ids.values()]]),
        )
        self.assertEqual(3, len(response.data))

    def test_registrations_multiple_users(self):
        ids = self.create_resubscribe_group()
        self.registrations_multiple_users_helper(ids)

    def test_registrations_multiple_users_autoresub(self):
        ids = self.create_auto_resubscribe_group()
        self.registrations_multiple_users_helper(ids, True)

    def test_registrations_put_resubscribe(self):
        self.create_auto_resubscribe_group(put=True)

    def delete_and_resub_helper(self, auto_resub, put, delete_before_sim_webhook):
        first_id = self.registration_cis120.id
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
            self.simulate_alert(self.cis120, 1, should_send=True)
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
            self.simulate_alert(self.cis120, 1, should_send=False)
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
                "You cannot resubscribe to a deleted registration.", response.data["detail"],
            )
        if not delete_before_sim_webhook:
            self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
            if auto_resub:
                self.assertFalse(
                    hasattr(
                        Registration.objects.get(id=first_id).resubscribed_to, "resubscribed_to",
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

    def cancel_and_resub_helper(self, auto_resub, put, cancel_before_sim_webhook):
        first_id = self.registration_cis120.id
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
            self.simulate_alert(self.cis120, 1, should_send=True)
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
            self.simulate_alert(self.cis120, 1, should_send=False)
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
                        Registration.objects.get(id=first_id).resubscribed_to, "resubscribed_to",
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
        first_id = self.registration_cis120.id
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
        first_id = self.registration_cis120.id
        self.simulate_alert(self.cis120, 1, should_send=True)
        response = self.client.put(
            reverse("registrations-detail", args=[first_id]),
            json.dumps({"cancelled": True}),
            content_type="application/json",
        )
        self.assertEquals(400, response.status_code)
        self.assertEquals("You cannot cancel a sent registration.", response.data["detail"])

    def test_delete_cancelled(self):
        first_id = self.registration_cis120.id
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
        first_id = self.registration_cis120.id
        if update_field == "resub":
            self.simulate_alert(self.cis120, 1)
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"resubscribe": True, "deleted": True, "auto_resubscribe": False,}),
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
                            "auto_resubscribe": False,
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
            self.assertFalse(Registration.objects.get(id=first_id).resubscribed_to.auto_resubscribe)
        if update_field == "deleted":
            if put:
                self.client.put(
                    reverse("registrations-detail", args=[first_id]),
                    json.dumps({"deleted": True, "auto_resubscribe": False}),
                    content_type="application/json",
                )
            else:
                self.client.post(
                    reverse("registrations-list"),
                    json.dumps({"id": first_id, "deleted": True, "auto_resubscribe": False}),
                    content_type="application/json",
                )
            self.assertTrue(Registration.objects.get(id=first_id).deleted)
            self.assertIsNotNone(Registration.objects.get(id=first_id).deleted_at)
            self.assertFalse(Registration.objects.get(id=first_id).auto_resubscribe)

    @data(*(((b, v), None) for b in (True, False) for v in ("resub", "deleted")))
    @unpack
    def test_changeattrs_update_order(self, value, result):
        self.changeattrs_update_order_helper(*value)

    def resub_attrs_maintained_helper(self, put):
        first_id = self.registration_cis120.id
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
        self.simulate_alert(self.cis120, 1)
        self.assertTrue(Registration.objects.get(id=first_id).notification_sent)
        self.assertFalse(Registration.objects.get(id=first_id).resubscribed_to.notification_sent)
        self.assertTrue(Registration.objects.get(id=first_id).auto_resubscribe)
        self.assertTrue(Registration.objects.get(id=first_id).resubscribed_to.auto_resubscribe)

    @data((True, None), (False, None))
    @unpack
    def test_resub_attrs_maintained(self, value, result):
        self.resub_attrs_maintained_helper(value)

    def delete_and_change_attrs_helper(self, put):
        first_id = self.registration_cis120.id
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
            "You cannot make changes to a deleted registration.", response.data["detail"],
        )

    @data((True, None), (False, None))
    @unpack
    def test_delete_and_change_attrs(self, value, result):
        self.delete_and_change_attrs_helper(value)

    def test_get_most_current_rec(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["first_id"]).get_most_current_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_most_current_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["third_id"]).get_most_current_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_most_current_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_most_current_rec(),
        )

    def test_get_original_registration_rec(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["first_id"]).get_original_registration_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_original_registration_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["third_id"]).get_original_registration_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_original_registration_rec(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_original_registration_rec(),
        )

    def test_get_resubscribe_group_sql(self):
        ids = self.create_resubscribe_group()
        first = Registration.objects.get(id=ids["first_id"])
        third = Registration.objects.get(id=ids["third_id"])
        fourth = Registration.objects.get(id=ids["third_id"])
        self.assertEqual(len(first.get_resubscribe_group_sql()), 3)
        self.assertEqual(len(third.get_resubscribe_group_sql()), 3)
        self.assertEqual(len(fourth.get_resubscribe_group_sql()), 3)
        self.assertTrue(first in third.get_resubscribe_group_sql())
        self.assertTrue(third in first.get_resubscribe_group_sql())
        self.assertTrue(first in fourth.get_resubscribe_group_sql())
        self.assertTrue(fourth in first.get_resubscribe_group_sql())
        self.assertTrue(third in fourth.get_resubscribe_group_sql())
        self.assertTrue(fourth in third.get_resubscribe_group_sql())

    def test_get_most_current_sql(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["first_id"]).get_most_current_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_most_current_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["third_id"]).get_most_current_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fourth_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_most_current_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_most_current_sql(),
        )

    def test_get_original_registration_sql(self):
        ids = self.create_resubscribe_group()
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["first_id"]).get_original_registration_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["second_id"]),
            Registration.objects.get(id=ids["second_id"]).get_original_registration_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["third_id"]).get_original_registration_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["first_id"]),
            Registration.objects.get(id=ids["fourth_id"]).get_original_registration_sql(),
        )
        self.assertEqual(
            Registration.objects.get(id=ids["fifth_id"]),
            Registration.objects.get(id=ids["fifth_id"]).get_original_registration_sql(),
        )
