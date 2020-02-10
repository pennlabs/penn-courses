import base64
import importlib
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from options.models import Option
from rest_framework.test import APIClient

from alert import tasks
from alert.models import SOURCE_API, SOURCE_PCA, Registration, RegStatus, register_for_course
from courses.models import PCA_REGISTRATION, APIKey, APIPrivilege, Course, StatusUpdate
from courses.util import create_mock_data, get_or_create_course_and_section


TEST_SEMESTER = '2019A'


def contains_all(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)


def set_semester():
    Option(key='SEMESTER', value=TEST_SEMESTER, value_type='TXT').save()


def override_delay(modules_names, before_func, before_kwargs):
    """
    A function that makes delay()ed functions synchronous for testing.  Please read the full docs (RTFM)
    before using to prevent unintended behavior or errors.
    See AlertRegistrationTestCase.simulate_alert for an example of how to use this function

    Args:
        modules_names: a list of 2-tuples of the form (module, name) where module is the module in which
            the delay()ed function is located and name is its name.  Note that each 2-tuple corresponds to
            exactly one delay()ed function.
            Make sure to order the delayed functions' 2-tuples in the
            modules_names list in the order that they will be executed.
            Also, note that each delay()ed function after the first must be
            triggered by the previous one (directly or indirectly).  Otherwise you could just
            call this function multiple times.  If this condition is not met, an error will be thrown.
            For more complicated use-cases (like patching functions between delay()ed functions),
            you will have to implement the functionality of this function yourself, in a custom way tailored to your
            use-case.
            Example of valid modules_names argument (from AlertRegistrationTestCase.simulate_alert):
                [('alert.tasks', 'send_course_alerts'), ('alert.tasks', 'send_alert')]
        before_func: a function (not its name, the actual function as a variable) which will be executed to trigger
            the first delay()ed function in modules_names.  Note that this function MUST trigger the first
            delay()ed function in modules_names or an error will be thrown.
            Example of a valid before_func argument (from AlertRegistrationTestCase.simulate_alert):
                a function simulating the webhook firing which causes send_course_alerts.delay() to be called
        before_kwargs: a dictionary of keyword-value arguments which will be unpacked and passed into before_func
    """
    if len(modules_names) > 0:
        mn = modules_names[-1]
        with patch(mn[0]+'.'+mn[1]+'.delay') as mock_func:
            mock_func.side_effect = getattr(importlib.import_module(mn[0]), mn[1])
            if len(modules_names) == 1:
                before_func(**before_kwargs)
            else:
                override_delay(modules_names[:-1], before_func, before_kwargs)


@patch('alert.models.Text.send_alert')
@patch('alert.models.Email.send_alert')
@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class SendAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        course, section = get_or_create_course_and_section('CIS-160-001', TEST_SEMESTER)
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


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class RegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.sections = []
        self.sections.append(get_or_create_course_and_section('CIS-160-001', TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section('CIS-160-002', TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section('CIS-120-001', TEST_SEMESTER)[1])

    def test_successful_registration(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual(self.sections[0].full_code, r.section.full_code)
        self.assertEqual('e@example.com', r.email)
        self.assertEqual('+15555555555', r.phone)
        self.assertFalse(r.notification_sent)
        self.assertEqual(SOURCE_PCA, r.source)
        self.assertIsNone(r.api_key)

    def test_nonnormalized_course_code(self):
        res, norm, _ = register_for_course('cis160001', 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual('CIS-160-001', norm)
        self.assertEqual(1, len(Registration.objects.all()))
        r = Registration.objects.get()
        self.assertEqual('CIS-160-001', r.section.full_code)

    def test_duplicate_registration(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(self.sections[0].full_code, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.OPEN_REG_EXISTS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_reregister(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0], notification_sent=True)
        r1.save()
        res, norm, _ = register_for_course(self.sections[0].full_code, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffsections(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(self.sections[1].full_code, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_sameuser_diffcourse(self):
        r1 = Registration(email='e@example.com', phone='+15555555555', section=self.sections[0])
        r1.save()
        res, norm, _ = register_for_course(self.sections[2].full_code, 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(2, len(Registration.objects.all()))

    def test_justemail(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, 'e@example.com', None)
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_phony_course(self):
        res, norm, _ = register_for_course('PHONY-100-001', 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.COURSE_NOT_FOUND, res)
        self.assertEqual(0, Registration.objects.count())

    def test_invalid_course(self):
        res, norm, _ = register_for_course('econ 0-0-1', 'e@example.com', '+15555555555')
        self.assertEqual(RegStatus.COURSE_NOT_FOUND, res)
        self.assertEqual(0, Registration.objects.count())

    def test_justphone(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, None, '5555555555')
        self.assertEqual(RegStatus.SUCCESS, res)
        self.assertEqual(1, len(Registration.objects.all()))

    def test_nocontact(self):
        res, norm, _ = register_for_course(self.sections[0].full_code, None, None)
        self.assertEqual(RegStatus.NO_CONTACT_INFO, res)
        self.assertEqual(0, len(Registration.objects.all()))


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class ResubscribeTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section = get_or_create_course_and_section('CIS-160-001', TEST_SEMESTER)
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


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class WebhookTriggeredAlertTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section = get_or_create_course_and_section('CIS-160-001', TEST_SEMESTER)
        self.r1 = Registration(email='e@example.com', phone='+15555555555', section=self.section)
        self.r2 = Registration(email='f@example.com', phone='+15555555556', section=self.section)
        self.r3 = Registration(email='g@example.com', phone='+15555555557', section=self.section)
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
        get_or_create_course_and_section('CIS-121-001', TEST_SEMESTER)
        result = tasks.get_active_registrations('CIS-121-001', TEST_SEMESTER)
        self.assertTrue(len(result) == 0)

    def test_collect_one(self):
        self.r2.notification_sent = True
        self.r3.notification_sent = True
        self.r2.save()
        self.r3.save()
        result_ids = [r.id for r in tasks.get_active_registrations(self.section.full_code, TEST_SEMESTER)]
        expected_ids = [self.r1.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)

    def test_collect_some(self):
        self.r2.notification_sent = True
        self.r2.save()
        result_ids = [r.id for r in tasks.get_active_registrations(self.section.full_code, TEST_SEMESTER)]
        expected_ids = [self.r1.id, self.r3.id]
        for id_ in expected_ids:
            self.assertTrue(id_ in result_ids)
        for id_ in result_ids:
            self.assertTrue(id_ in expected_ids)


@patch('alert.views.alert_for_course')
@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
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

    def test_alert_called_and_sent_intl(self, mock_alert):
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps({
                'course_section': 'INTLBUL001',
                'previous_status': 'X',
                'status': 'O',
                'status_code_normalized': 'Open',
                'term': TEST_SEMESTER
            }),
            content_type='application/json',
            **self.headers)

        self.assertEqual(200, res.status_code)
        self.assertTrue(mock_alert.called)
        self.assertEqual('INTLBUL001', mock_alert.call_args[0][0])
        self.assertEqual('2019A', mock_alert.call_args[1]['semester'])
        self.assertTrue('sent' in json.loads(res.content)['message'])
        self.assertEqual(1, StatusUpdate.objects.count())
        u = StatusUpdate.objects.get()
        self.assertTrue(u.alert_sent)

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


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class APIRegisterTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.client = Client()
        self.course, self.section = get_or_create_course_and_section('CIS-120-001', TEST_SEMESTER)
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


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, cis120_section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        _, cis160_section = create_mock_data('CIS-160-001', TEST_SEMESTER)
        self.statusUpdates = [StatusUpdate(section=cis120_section,
                                           old_status='O',
                                           new_status='C',
                                           alert_sent=False),
                              StatusUpdate(section=cis120_section,
                                           old_status='C',
                                           new_status='O',
                                           alert_sent=True),
                              StatusUpdate(section=cis160_section,
                                           old_status='C',
                                           new_status='O',
                                           alert_sent=True)
                              ]
        for s in self.statusUpdates:
            s.save()
        self.client = APIClient()

    def test_cis120(self):
        response = self.client.get('/statusupdate/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[0]['old_status'], 'O')
        self.assertEqual(response.data[0]['new_status'], 'C')
        self.assertEqual(response.data[0]['alert_sent'], False)
        self.assertFalse(hasattr(response.data[0], 'request_body'))
        self.assertEqual(response.data[1]['old_status'], 'C')
        self.assertEqual(response.data[1]['new_status'], 'O')
        self.assertEqual(response.data[1]['alert_sent'], True)
        self.assertFalse(hasattr(response.data[1], 'request_body'))

    def test_cis160(self):
        response = self.client.get('/statusupdate/CIS-160/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['old_status'], 'C')
        self.assertEqual(response.data[0]['new_status'], 'O')
        self.assertEqual(response.data[0]['alert_sent'], True)
        self.assertFalse(hasattr(response.data[0], 'request_body'))

    def test_cis121_missing(self):
        response = self.client.get('/statusupdate/CIS-121/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class UserDetailTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username='jacob',
                                 password='top_secret')
        self.client = APIClient()
        self.client.login(username='jacob', password='top_secret')

    def test_settings_before_create(self):
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('jacob', response.data['username'])
        self.assertEqual('', response.data['first_name'])
        self.assertEqual('', response.data['last_name'])
        self.assertEqual(None, response.data['profile']['email'])
        self.assertEqual(None, response.data['profile']['phone'])

    def test_update_settings(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_update_settings_change_first_name(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'first_name': 'newname', 'last_name': '',
                                               'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'newname')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'newname')
        self.assertEqual(response.data['last_name'], '')

    def test_update_settings_change_last_name(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'first_name': '', 'last_name': 'newname',
                                               'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], 'newname')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], 'newname')

    def test_update_settings_change_username(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'username': 'newusername', 'first_name': '', 'last_name': '',
                                               'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_add_fields(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'first_name': '', 'last_name': '',
                                               'middle_name': 'm',
                                               'profile': {'email': 'example@email.com', 'phone': '3131234567',
                                                           'favorite_color': 'blue'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertFalse('favorite_color' in response.data['profile'])
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        self.assertFalse('middle_name' in response.data)
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertFalse('favorite_color' in response.data['profile'])
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        self.assertFalse('middle_name' in response.data)

    def test_ignore_fields_email_update(self):
        self.client.put('/api/settings/',
                        json.dumps({'first_name': 'fname', 'last_name': 'lname',
                                    'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                        content_type='application/json')
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example2@email.com'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example2@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'fname')
        self.assertEqual(response.data['last_name'], 'lname')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example2@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'fname')
        self.assertEqual(response.data['last_name'], 'lname')

    def test_ignore_fields_phone_update(self):
        self.client.put('/api/settings/',
                        json.dumps({'first_name': 'fname', 'last_name': 'lname',
                                    'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                        content_type='application/json')
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'phone': '2121234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['phone'], '+12121234567')
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'fname')
        self.assertEqual(response.data['last_name'], 'lname')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['phone'], '+12121234567')
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], 'fname')
        self.assertEqual(response.data['last_name'], 'lname')

    def test_invalid_phone(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example@email.com', 'phone': 'abc'}}),
                                   content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data['profile']['email'])
        self.assertEqual(None, response.data['profile']['phone'])
        self.assertEqual('jacob', response.data['username'])
        self.assertEqual('', response.data['first_name'])
        self.assertEqual('', response.data['last_name'])

    def test_invalid_email(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example@', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data['profile']['email'])
        self.assertEqual(None, response.data['profile']['phone'])
        self.assertEqual('jacob', response.data['username'])
        self.assertEqual('', response.data['first_name'])
        self.assertEqual('', response.data['last_name'])

    def test_null_email(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': None, 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], None)
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], None)
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_null_phone(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example@email.com', 'phone': None}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], None)
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], None)
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_both_null(self):
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': None, 'phone': None}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], None)
        self.assertEqual(response.data['profile']['phone'], None)
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], None)
        self.assertEqual(response.data['profile']['phone'], None)
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_multiple_users_independent(self):
        User.objects.create_user(username='murey',
                                 password='top_secret')
        client2 = APIClient()
        client2.login(username='murey', password='top_secret')
        response = self.client.put('/api/settings/',
                                   json.dumps({'profile': {'email': 'example@email.com', 'phone': '3131234567'}}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = self.client.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example@email.com')
        self.assertEqual(response.data['profile']['phone'], '+13131234567')
        self.assertEqual(response.data['username'], 'jacob')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = client2.put('/api/settings/',
                               json.dumps({'profile': {'email': 'example2@email.com', 'phone': '2121234567'}}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['email'], 'example2@email.com')
        self.assertEqual(response.data['profile']['phone'], '+12121234567')
        self.assertEqual(response.data['username'], 'murey')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')
        response = client2.get('/api/settings/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['profile']['email'], 'example2@email.com')
        self.assertEqual(response.data['profile']['phone'], '+12121234567')
        self.assertEqual(response.data['username'], 'murey')
        self.assertEqual(response.data['first_name'], '')
        self.assertEqual(response.data['last_name'], '')

    def test_user_not_logged_in(self):
        client2 = APIClient()
        response = client2.put('/api/settings/',
                               json.dumps({'profile': {'email': 'example2@email.com', 'phone': '2121234567'}}),
                               content_type='application/json')
        self.assertEqual(403, response.status_code)
        response = client2.get('/api/settings/')
        self.assertEqual(403, response.status_code)


@override_settings(ROOT_URLCONF='PennCourses.urls.pca')
class AlertRegistrationTestCase(TestCase):
    def setUp(self):
        set_semester()
        Option.objects.update_or_create(key='SEND_FROM_WEBHOOK', value_type='BOOL', defaults={'value': 'TRUE'})
        self.user = User.objects.create_user(username='jacob',
                                             password='top_secret')
        self.user.save()
        self.user.profile.email = 'j@gmail.com'
        self.user.profile.phone = '+11234567890'
        self.user.profile.save()
        self.client = APIClient()
        self.client.login(username='jacob', password='top_secret')
        _, self.cis120 = create_mock_data('CIS-120-001', TEST_SEMESTER)
        _, self.cis160 = create_mock_data('CIS-160-001', TEST_SEMESTER)
        _, self.cis121 = create_mock_data('CIS-121-001', TEST_SEMESTER)
        response = self.client.post('/api/registrations/',
                                    json.dumps({'section': 'CIS-120-001',
                                                'auto_resubscribe': False}),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)
        self.registration_cis120 = Registration.objects.get(section=self.cis120)

    @staticmethod
    def convert_date(date):
        return parse_datetime(date) if date is not None else None

    def check_model_with_response_data(self, model, data):
        self.assertEqual(model.id, data['id'])
        self.assertEqual(model.user.username, data['user'])
        self.assertEqual(model.section.full_code, data['section'])
        self.assertEqual(model.deleted, data['deleted'])
        self.assertEqual(model.deleted_at, self.convert_date(data['deleted_at']))
        self.assertEqual(model.auto_resubscribe, data['auto_resubscribe'])
        self.assertEqual(model.notification_sent, data['notification_sent'])
        self.assertEqual(model.notification_sent_at, self.convert_date(data['notification_sent_at']))
        self.assertEqual(model.created_at, self.convert_date(data['created_at']))
        self.assertEqual(model.updated_at, self.convert_date(data['updated_at']))

    def check_model_with_raw_queryset(self, model, qs):
        self.assertEqual(model.id, qs.id)
        self.assertEqual(model.user.username, qs.user.username)
        self.assertEqual(model.section.full_code, qs.section.full_code)
        self.assertEqual(model.deleted, qs.deleted)
        self.assertEqual(model.deleted_at, model.deleted_at)
        self.assertEqual(model.auto_resubscribe, model.auto_resubscribe)
        self.assertEqual(model.notification_sent, qs.notification_sent)
        self.assertEqual(model.notification_sent_at, qs.notification_sent_at)
        self.assertEqual(model.created_at, qs.created_at)
        self.assertEqual(model.updated_at, qs.updated_at)

    def simulate_alert_helper_before(self, section):
        auth = base64.standard_b64encode('webhook:password'.encode('ascii'))
        headers = {
            'Authorization': f'Basic {auth.decode()}',
        }
        body = {
            'course_section': section.full_code.replace('-', ''),
            'previous_status': 'X',
            'status': 'O',
            'status_code_normalized': 'Open',
            'term': section.semester
        }
        res = self.client.post(
            reverse('webhook', urlconf='alert.urls'),
            data=json.dumps(body),
            content_type='application/json',
            **headers)
        self.assertEqual(200, res.status_code)
        self.assertTrue('sent' in json.loads(res.content)['message'])

    def simulate_alert(self, section, num_status_updates=1):
        with patch('alert.alerts.send_email', return_value=True) as send_email_mock:
            with patch('alert.alerts.send_text', return_value=True) as send_text_mock:
                override_delay([('alert.tasks', 'send_course_alerts'), ('alert.tasks', 'send_alert')],
                               self.simulate_alert_helper_before, {'section': section})
                self.assertEqual(1, send_email_mock.call_count)
                self.assertEqual(1, send_text_mock.call_count)
                self.assertEqual('+11234567890', send_text_mock.call_args[0][0])
                self.assertEqual('j@gmail.com', send_email_mock.call_args[1]['to'])
                for r in Registration.objects.filter(section=section):
                    self.assertTrue(r.notification_sent)
                    self.assertIsNotNone(r.notification_sent_at)
                self.assertEqual(num_status_updates, StatusUpdate.objects.count())
                for u in StatusUpdate.objects.all():
                    self.assertTrue(u.alert_sent)

    def test_registrations_get_most_current(self):
        response = self.client.get(f'/api/registrations/{self.registration_cis120.pk}/')
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(self.registration_cis120, response.data)

    def test_registrations_resubscribe_get_old_and_history(self):
        response = self.client.post('/api/registrations/',
                                    json.dumps({'section': 'CIS-160-001',
                                                'auto_resubscribe': False}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get(f'/api/registrations/{response.data["id"]}/')
        self.assertEqual(response.status_code, 200)
        self.check_model_with_response_data(Registration.objects.get(id=2), response.data)
        self.simulate_alert(self.cis120, 1)
        response = self.client.post('/api/registrations/',
                                    json.dumps({'id': 1,
                                                'resubscribe': True}),
                                    content_type='application/json')
        self.registration_cis120 = Registration.objects.get(id=1)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/registrations/1/')
        self.assertEqual(200, response.status_code)
        self.check_model_with_response_data(self.registration_cis120.resubscribed_to, response.data)
        self.simulate_alert(self.cis120, 2)
        response = self.client.post('/api/registrations/',
                                    json.dumps({'id': 3,
                                                'resubscribe': True}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/api/registrations/',
                                    json.dumps({'section': 'CIS-121-001',
                                                'auto_resubscribe': False}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.registration_cis120 = Registration.objects.get(id=1)
        response = self.client.get('/api/registrations/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(response.data))
        fourth_data = next(item for item in response.data if item['id'] == 4)
        second_data = next(item for item in response.data if item['id'] == 2)
        fifth_data = next(item for item in response.data if item['id'] == 5)
        self.check_model_with_response_data(self.registration_cis120.resubscribed_to.resubscribed_to, fourth_data)
        self.check_model_with_response_data(Registration.objects.get(id=2), second_data)
        self.check_model_with_response_data(Registration.objects.get(id=5), fifth_data)
        response = self.client.get('/api/registrationhistory/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(5, len(response.data))
        first_data = next(item for item in response.data if item['id'] == 1)
        first_ob = Registration.objects.get(id=1)
        self.check_model_with_response_data(self.registration_cis120, first_data)
        self.assertIsNone(first_ob.resubscribed_from)
        self.assertTrue(self.registration_cis120.notification_sent)
        self.assertIsNotNone(self.registration_cis120.notification_sent_at)
        second_data = next(item for item in response.data if item['id'] == 2)
        second_ob = Registration.objects.get(id=2)
        self.check_model_with_response_data(second_ob, second_data)
        self.assertIsNone(second_ob.resubscribed_from)
        self.assertFalse(hasattr(second_ob, 'resubscribed_to'))
        self.assertFalse(second_data['notification_sent'])
        self.assertIsNone(second_data['notification_sent_at'])
        third_data = next(item for item in response.data if item['id'] == 3)
        third_ob = Registration.objects.get(id=3)
        self.assertEquals(self.registration_cis120.resubscribed_to, Registration.objects.get(id=3))
        self.assertEquals(first_ob, third_ob.resubscribed_from)
        self.check_model_with_response_data(self.registration_cis120.resubscribed_to, third_data)
        self.assertTrue(third_data['notification_sent'])
        self.assertIsNotNone(third_data['notification_sent_at'])
        fourth_data = next(item for item in response.data if item['id'] == 4)
        fourth_ob = Registration.objects.get(id=4)
        self.assertEquals(self.registration_cis120.resubscribed_to.resubscribed_to, fourth_ob)
        self.check_model_with_response_data(self.registration_cis120.resubscribed_to.resubscribed_to, fourth_data)
        self.assertEquals(third_ob, fourth_ob.resubscribed_from)
        self.assertFalse(hasattr(fourth_ob, 'resubscribed_to'))
        self.assertFalse(fourth_data['notification_sent'])
        self.assertIsNone(fourth_data['notification_sent_at'])
        fifth_data = next(item for item in response.data if item['id'] == 5)
        fifth_ob = Registration.objects.get(id=5)
        self.check_model_with_response_data(fifth_ob, fifth_data)
        self.assertIsNone(fifth_ob.resubscribed_from)
        self.assertFalse(hasattr(fifth_ob, 'resubscribed_to'))
        self.assertFalse(fifth_data['notification_sent'])
        self.assertIsNone(fifth_data['notification_sent_at'])

    def test_get_resubscribe_group(self):
        self.client.post('/api/registrations/',
                         json.dumps({'section': 'CIS-160-001',
                                     'auto_resubscribe': False}),
                         content_type='application/json')
        self.simulate_alert(self.cis120, 1)
        self.client.post('/api/registrations/',
                         json.dumps({'id': 1,
                                     'resubscribe': True}),
                         content_type='application/json')
        self.simulate_alert(self.cis120, 2)
        self.client.post('/api/registrations/',
                         json.dumps({'id': 3,
                                     'resubscribe': True}),
                         content_type='application/json')
        self.client.post('/api/registrations/',
                         json.dumps({'section': 'CIS-121-001',
                                     'auto_resubscribe': False}),
                         content_type='application/json')
        self.registration_cis120 = Registration.objects.get(id=1)
        first = Registration.objects.get(id=1)
        second = Registration.objects.get(id=3)
        third = Registration.objects.get(id=4)
        self.assertEqual(len(first.get_resubscribe_group()), 3)
        self.assertEqual(len(second.get_resubscribe_group()), 3)
        self.assertEqual(len(third.get_resubscribe_group()), 3)
        self.assertTrue(first in second.get_resubscribe_group())
        self.assertTrue(second in first.get_resubscribe_group())
        self.assertTrue(first in third.get_resubscribe_group())
        self.assertTrue(third in first.get_resubscribe_group())
        self.assertTrue(second in third.get_resubscribe_group())
        self.assertTrue(third in second.get_resubscribe_group())

    def test_get_most_current(self):
        pass

    def test_get_original_registration(self):
        pass

    def test_get_most_current_rec(self):
        pass

    def test_registrations_list_only_current(self):
        pass

    def test_registrations_multiple_users(self):
        pass

    def test_registrations_post(self):
        pass

    def test_registrations_put(self):
        pass

    def test_registrations_post_changeattrs(self):
        pass

    def test_registrations_post_delete(self):
        pass

    def test_registrations_post_resubscribe(self):
        pass

    def test_registrations_get_most_current_after_resubscribe(self):
        pass

# replace recursive get most current with SQL query in gets / puts (change method), and resubscribe (add method)

# test manage.py loadhistory command

# test course status update hook

# fix plan list order

# test integration with other code, Davis (UserDetail)
