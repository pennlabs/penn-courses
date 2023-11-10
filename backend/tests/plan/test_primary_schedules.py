from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from courses.models import Friendship
from plan.models import PrimarySchedule, Schedule
from tests.alert.test_alert import TEST_SEMESTER, set_semester
from tests.courses.util import create_mock_data_with_reviews


primary_schedule_url = "/api/plan/primary-schedules/"


class PrimaryScheduleTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username="jacobily", email="jacob@example.com", password="top_secret"
        )
        set_semester()
        _, self.cis120, self.cis120_reviews = create_mock_data_with_reviews(
            "CIS-120-001", TEST_SEMESTER, 2
        )
        _, self.cis121, self.cis121_reviews = create_mock_data_with_reviews(
            "CIS-121-001", TEST_SEMESTER, 2
        )
        self.s = Schedule(
            person=self.u1,
            semester=TEST_SEMESTER,
            name="My Test Schedule",
        )
        self.s.save()
        self.s.sections.set([self.cis120])

        self.s2 = Schedule(
            person=self.u1,
            semester=TEST_SEMESTER,
            name="My Test Schedule 2",
        )
        self.s2.save()
        self.s2.sections.set([self.cis121])

        to_delete = Schedule(
            person=self.u1,
            semester=TEST_SEMESTER,
            name="My Test Schedule To Delete",
        )
        to_delete.save()
        self.deleted_schedule_id = to_delete.id
        to_delete.delete()

        self.client = APIClient()
        self.client.login(username="jacobily", password="top_secret")

    def assert_primary_schedule_id(self, client, user, schedule_id, num_primary=None):
        if schedule_id is None:
            self.assertEqual(PrimarySchedule.objects.filter(user=user).count(), 0)
        else:
            self.assertEqual(PrimarySchedule.objects.get(user=user).schedule_id, schedule_id)
        response = client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        if num_primary is not None:
            self.assertEqual(len(response.json()), num_primary)
        if schedule_id is not None:
            self.assertIn(schedule_id, [p["schedule"]["id"] for p in response.json()])

    def test_post_primary_schedule(self):
        response = self.client.post(primary_schedule_url, {"schedule_id": self.s.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client, self.u1, self.s.id, num_primary=1)

    def test_invalid_schedule_id(self):
        response = self.client.post(primary_schedule_url, {"schedule_id": self.deleted_schedule_id})
        self.assertEqual(response.status_code, 400)
        self.assert_primary_schedule_id(self.client, self.u1, None, num_primary=0)

    def test_replace_primary_schedule(self):
        response = self.client.post(primary_schedule_url, {"schedule_id": self.s.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client, self.u1, self.s.id, num_primary=1)

        response = self.client.post(primary_schedule_url, {"schedule_id": self.s2.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client, self.u1, self.s2.id, num_primary=1)

    def test_unset_primary_schedule(self):
        response = self.client.post(primary_schedule_url, {"schedule_id": self.s.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client, self.u1, self.s.id, num_primary=1)

        response = self.client.post(primary_schedule_url, {"schedule_id": ""})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client, self.u1, None, num_primary=0)

    def test_primary_schedule_friends(self):
        response = self.client.post(primary_schedule_url, {"schedule_id": self.s.id})

        u2 = User.objects.create_user(
            username="jacob2", email="jacob2@gmail.com", password="top_secret"
        )
        u3 = User.objects.create_user(
            username="jacob3", email="jacob3@gmail.com", password="top_secret"
        )
        self.client2 = APIClient()
        self.client2.login(username="jacob2", password="top_secret")
        self.client3 = APIClient()
        self.client3.login(username="jacob3", password="top_secret")

        Friendship.objects.create(sender=self.u1, recipient=u2, status=Friendship.Status.ACCEPTED)
        u2_s = Schedule(
            person=u2,
            semester=TEST_SEMESTER,
            name="U2 Test Schedule",
        )
        u2_s.save()
        u2_s.sections.set([self.cis120])
        response = self.client2.post(primary_schedule_url, {"schedule_id": u2_s.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client2, u2, u2_s.id, num_primary=2)

        response = self.client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertIn(self.s.id, [p["schedule"]["id"] for p in response.json()])
        self.assertIn(u2_s.id, [p["schedule"]["id"] for p in response.json()])

        Friendship.objects.create(sender=self.u1, recipient=u3, status=Friendship.Status.ACCEPTED)
        u3_s = Schedule(
            person=u3,
            semester=TEST_SEMESTER,
            name="U3 Test Schedule",
        )
        u3_s.save()
        u3_s.sections.set([self.cis120])

        # shouldn't change bc no primary scheudle for u3 yet
        response = self.client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

        # add a primary schedule for u3
        response = self.client3.post(primary_schedule_url, {"schedule_id": u3_s.id})
        self.assertEqual(response.status_code, 200)
        self.assert_primary_schedule_id(self.client3, u3, u3_s.id, num_primary=2)

        # u1 should have all 3 now
        self.assert_primary_schedule_id(self.client, self.u1, self.s.id, num_primary=3)

        # remove u2 as a friend
        friendshipu2 = Friendship.objects.get(sender=self.u1, recipient=u2)
        friendshipu2.delete()

        # only have u1 and u3 now
        self.assert_primary_schedule_id(self.client, self.u1, self.s.id, num_primary=2)
        self.assert_primary_schedule_id(self.client2, u2, u2_s.id, num_primary=1)
        self.assert_primary_schedule_id(self.client3, u3, u3_s.id, num_primary=2)
