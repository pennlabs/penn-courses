import base64
import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from alert import tasks
from alert.models import SOURCE_API, SOURCE_PCA, Registration, RegStatus, get_course_and_section, register_for_course
from courses.models import PCA_REGISTRATION, APIKey, APIPrivilege, Course, StatusUpdate
from courses.util import record_update, update_course_from_record
from options.models import Option


TEST_SEMESTER = '2019A'


def contains_all(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


def set_semester():
    Option(key='SEMESTER', value=TEST_SEMESTER, value_type='TXT').save()


@patch('alert.models.Text.send_alert')
@patch('alert.models.Email.send_alert')
@override_settings(SWITCHBOARD_TEST_APP='pca')
class SendAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        course, section = get_course_and_section('CIS-160-001', TEST_SEMESTER)
        self.r = Registration(email='yo@example.com',
                              phone='+15555555555',
                              section=section)

        self.r.save()

    def test_send_alert(self, mock_email, mock_text):
        self.assertFalse(Registration.objects.get(id=self.r.id).notification_sent)
        tasks.send_alert(self.r.id, sent_by='ADM')
        self.assertTrue(mock_email.called)
        self.assertTrue(mock_text.called)
        self.assertTrue(Registration.objects.get(id=self.r.id).notification_sent)
        self.assertEqual('ADM', Registration.objects.get(id=self.r.id).notification_sent_by)

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


@override_settings(SWITCHBOARD_TEST_APP='pca')
class RegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.sections = []
        self.sections.append(get_course_and_section('CIS-160-001', TEST_SEMESTER)[1])
        self.sections.append(get_course_and_section('CIS-160-002', TEST_SEMESTER)[1])
        self.sections.append(get_course_and_section('CIS-120-001', TEST_SEMESTER)[1])

    def test_successful_registration(self):
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual(self.sections[0].normalized, r.section.normalized)
        self.assertEqual('e@example.com', r.email)
        self.assertEqual('+15555555555', r.phone)
        self.assertFalse(r.notification_sent)
        self.assertEqual(SOURCE_PCA, r.source)
        self.assertIsNone(r.api_key)

    def test_duplicate_registration(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.OPEN_REG_EXISTS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_reregister(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0], notification_sent=True)
        r1.save()
        res = register_for_course(self.sections[0].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffsections(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[1].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffcourse(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res = register_for_course(self.sections[2].normalized, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_justemail(self):
        res = register_for_course(self.sections[0].normalized, 'e@example.com', None)
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_justphone(self):
        res = register_for_course(self.sections[0].normalized, None, '5555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_nocontact(self):
        res = register_for_course(self.sections[0].normalized, None, None)
        self.assertEqual(RegStatus.NO_CONTACT_INFO, res)
        self.assertEqual(0, len(Registration.objects.all()))


@override_settings(SWITCHBOARD_TEST_APP='pca')
class ResubscribeTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section = get_course_and_section('CIS-160-001', TEST_SEMESTER)
        self.base_reg = Registration(email='e@example.com', phone='+15555555555', section=self.section)
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
        reg1 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=self.base_reg,
                            notification_sent=True)
        reg1.save()
        reg2 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg1,
                            notification_sent=True)
        reg2.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result.resubscribed_from, reg2)

    def test_resubscribe_oldlink_noalert(self):
        """testing idempotence on old links"""
        self.base_reg.notification_sent = True
        self.base_reg.save()
        reg1 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=self.base_reg,
                            notification_sent=True)
        reg1.save()
        reg2 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg1,
                            notification_sent=True)
        reg2.save()
        reg3 = Registration(email='e@example.com',
                            phone='+15555555555',
                            section=self.section,
                            resubscribed_from=reg2,
                            notification_sent=False)
        reg3.save()

        result = self.base_reg.resubscribe()
        self.assertEqual(4, len(Registration.objects.all()))
        self.assertEqual(result, reg3)


@override_settings(SWITCHBOARD_TEST_APP='pca')
class WebhookTriggeredAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section = get_course_and_section('CIS-160-001', TEST_SEMESTER)
        self.r1 = Registration(email='e@example.com', phone='+15555555555', section=self.section)
        self.r2 = Registration(email='f@example.com', phone='+15555555556', section=self.section)
        self.r3 = Registration(email='g@example.com', phone='+15555555557', section=self.section)
        self.r1.save()
        self.r2.save()
        self.r3.save()

    def test_collect_all(self):
        result = tasks.get_active_registrations(self.section.normalized, TEST_SEMESTER)
        expected_ids = [r.id for r in [self.r1, self.r2, self.r3]]
        result_ids = [r.id for r in result]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)

        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_none(self):
        get_course_and_section('CIS-121-001', TEST_SEMESTER)
        result = tasks.get_active_registrations('CIS-121-001', TEST_SEMESTER)
        self.assertTrue(len(result) == 0)

    def test_collect_one(self):
        self.r2.notification_sent = True
        self.r3.notification_sent = True
        self.r2.save()
        self.r3.save()
        result_ids = [r.id for r in tasks.get_active_registrations(self.section.normalized, TEST_SEMESTER)]
        expected_ids = [self.r1.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_some(self):
        self.r2.notification_sent = True
        self.r2.save()
        result_ids = [r.id for r in tasks.get_active_registrations(self.section.normalized, TEST_SEMESTER)]
        expected_ids = [self.r1.id, self.r3.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)


@patch('alert.views.alert_for_course')
@override_settings(SWITCHBOARD_TEST_APP='pca')
class WebhookViewTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.client = Client()
        auth = base64.standard_b64encode('webhook:password'.encode('ascii'))
        self.headers = {
            'Authorization': f'Basic {auth.decode()}',
        }
        self.body = {
            'course_section': 'ANTH361401',
            'previous_status': 'X',
            'status': 'O',
            'status_code_normalized': 'Open',
            'term': TEST_SEMESTER
        }
        Option.objects.update_or_create(key='SEND_FROM_WEBHOOK', value_type='BOOL', defaults={'value': 'TRUE'})
        Option.objects.update_or_create(key='SEMESTER', value_type='TXT', defaults={'value': TEST_SEMESTER})

    def test_alert_called_and_sent(self, mock_alert):
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)

        self.assertEqual(200, res.status_code)
        self.assertTrue(mock_alert.called)
        self.assertEqual('ANTH361401', mock_alert.call_args[0][0])
        self.assertEqual('2019A', mock_alert.call_args[1]['semester'])
        self.assertTrue('sent' in json.loads(res.content)['message'])
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertTrue(u.alert_sent)

    def test_alert_bad_json(self, mock_alert):
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data='blah',
            content_type='application/json',
            **self.headers)

        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_alert_called_closed_course(self, mock_alert):
        self.body['status'] = 'C'
        self.body['status_code_normalized'] = 'Closed'
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)

        self.assertEqual(200, res.status_code)
        self.assertFalse('sent' in json.loads(res.content)['message'])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_alert_called_wrong_sem(self, mock_alert):
        self.body['term'] = 'NOTRM'
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)

        self.assertEqual(200, res.status_code)
        self.assertFalse('sent' in json.loads(res.content)['message'])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_alert_called_alerts_off(self, mock_alert):
        Option.objects.update_or_create(key='SEND_FROM_WEBHOOK', value_type='BOOL', defaults={'value': 'FALSE'})
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)

        self.assertEqual(200, res.status_code)
        self.assertFalse('sent' in json.loads(res.content)['message'])
        self.assertFalse(mock_alert.called)
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertFalse(u.alert_sent)

    def test_bad_format(self, mock_alert):
        self.body = {'hello': 'world'}
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps({
                'hello': 'world'
            }),
            content_type='application/json',
            **self.headers)
        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_no_status(self, mock_alert):
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps({
                'course_section': 'ANTH361401',
                'previous_status': 'X',
                'status_code_normalized': 'Open',
                'term': '2019A'
            }),
            content_type='application/json',
            **self.headers)
        self.assertEqual(400, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_method(self, mock_alert):
        res = self.client.get(reverse('webhook', urlconf='alert.urls'), **self.headers)
        self.assertEqual(405, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_content(self, mock_alert):
        res = self.client.post(reverse('webhook', urlconf='alert.urls'),
                               **self.headers)
        self.assertEqual(415, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_password(self, mock_alert):
        self.headers['Authorization'] = 'Basic ' + base64.standard_b64encode('webhook:abc123'.encode('ascii')).decode()
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)
        self.assertEqual(401, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())

    def test_wrong_user(self, mock_alert):
        self.headers['Authorization'] = (
            'Basic ' + base64.standard_b64encode('baduser:password'.encode('ascii')).decode()
        )
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(self.body),
            content_type='application/json',
            **self.headers)
        self.assertEqual(401, res.status_code)
        self.assertFalse(mock_alert.called)
        self.assertEqual(0, StatusUpdate.objects.count())


@override_settings(SWITCHBOARD_TEST_APP='pca')
class APIRegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.client = Client()
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.permission = APIPrivilege.objects.create(code=PCA_REGISTRATION)
        self.key = APIKey.objects.get_or_create(email='contact@penncoursenotify.com')[0]
        self.key.privileges.add(self.permission)
        self.headers = {
            'Authorization': 'Bearer ' + str(self.key.code)
        }

    def test_successful_registration(self):
        body = {
            'email': 'student@example.com',
            'course': 'CIS 120 001',
        }
        res = self.client.post(
            reverse('api-register', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, Registration.objects.count())
        self.assertEqual(1, Course.objects.count())
        self.assertEqual(SOURCE_API, Registration.objects.get().source)
        self.assertEqual(self.key, Registration.objects.get().api_key)

    def test_invalid_api_key(self):
        body = {
            'email': 'student@example.com',
            'course': 'CIS 120 001',
        }
        res = self.client.post(
            reverse('api-register', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
            **{'Authorization': 'Bearer blargh'}
        )
        self.assertEqual(401, res.status_code)
        self.assertEqual(0, Registration.objects.count())

    def test_no_api_key(self):
        body = {
            'email': 'student@example.com',
            'course': 'CIS 120 001',
        }
        res = self.client.post(
            reverse('api-register', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
        )
        self.assertEqual(401, res.status_code)
        self.assertEqual(0, Registration.objects.count())

    def test_inactive_key(self):
        self.key.active = False
        self.key.save()
        body = {
            'email': 'student@example.com',
            'course': 'CIS 120 001',
        }
        res = self.client.post(
            reverse('api-register', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(401, res.status_code)
        self.assertEqual(0, Registration.objects.count())

    def test_no_permission(self):
        self.key.privileges.clear()
        body = {
            'email': 'student@example.com',
            'course': 'CIS 120 001',
        }
        res = self.client.post(
            reverse('api-register', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
            **self.headers
        )
        self.assertEqual(401, res.status_code)
        self.assertEqual(0, Registration.objects.count())


@override_settings(SWITCHBOARD_TEST_APP='pca')
class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)

    def test_update_status(self):
        self.section.status = 'C'
        self.section.save()
        up = record_update(self.section.normalized,
                           TEST_SEMESTER,
                           'C',
                           'O',
                           True,
                           'JSON')
        up.save()
        update_course_from_record(up)
        _, section = get_course_and_section(self.section.normalized, TEST_SEMESTER)
        self.assertEqual('O', section.status)
