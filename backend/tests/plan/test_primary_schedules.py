from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from courses.models import Friendship
from plan.models import Schedule
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

    def test_put_primary_schedule(self):
        response = self.client.put(primary_schedule_url, {"schedule_id": self.s.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.s.id)
        self.assertEqual(response.json()["name"], self.s.name)
        self.assertEqual(response.json()["sections"][0]["id"], self.cis120.id)
        self.assertEqual(response.json()["sections"][0]["course"]["id"], self.cis120.course.id)

    def test_replace_primary_schedule(self):
        response = self.client.put(primary_schedule_url, {"schedule_id": self.deleted_schedule_id})  # invalid ID

        self.assertEqual(response.status_code, 400)

        response = self.client.put(primary_schedule_url, {"schedule_id": self.s.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.s.id)

        response = self.client.put(primary_schedule_url, {"schedule_id": self.s2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.s2.id)

    def test_primary_schedule_friends(self):
        response = self.client.put(primary_schedule_url, {"schedule_id": self.s.id})

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
        response = self.client2.put(primary_schedule_url, {"schedule_id": u2_s.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], u2_s.id)

        response = self.client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["id"], self.s.id)
        self.assertEqual(response.json()[1]["id"], u2_s.id)

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
        response = self.client3.put(primary_schedule_url, {"schedule_id": u3_s.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], u3_s.id)

        # should have all 3 now
        response = self.client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

        # remove u2 as a friend
        friendshipu2 = Friendship.objects.get(sender=self.u1, recipient=u2)
        friendshipu2.delete()

        # only have u1 and u3 now
        response = self.client.get(primary_schedule_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["id"], self.s.id)
        self.assertEqual(response.json()[1]["id"], u3_s.id)
