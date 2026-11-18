from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from degree.models import DegreePlan, PDPBetaUser


class PlanLimitTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="t", password="x")
        PDPBetaUser.objects.create(person=self.user)
        self.client = APIClient()
        self.client.force_login(self.user)
        self.plans = [
            DegreePlan.objects.create(name=f"Plan {i}", person=self.user)
            for i in range(DegreePlan.MAX_PER_USER - 1)
        ]

    def create(self, name):
        return self.client.post(reverse("degreeplan-list"), {"name": name}, format="json")

    def copy(self, name):
        return self.client.post(
            reverse("degreeplan-copy", kwargs={"pk": self.plans[0].id}),
            {"name": name},
            format="json",
        )

    def test_creating_up_to_the_limit(self):
        self.assertEqual(self.create("Last").status_code, 201)
        response = self.create("One too many")
        self.assertEqual(response.status_code, 400)
        self.assertIn("up to 10", str(response.json()))
        self.assertEqual(DegreePlan.objects.filter(person=self.user).count(), 10)

    def test_copying_up_to_the_limit(self):
        self.assertEqual(self.copy("Last").status_code, 201)
        self.assertEqual(self.copy("One too many").status_code, 400)
        self.assertEqual(DegreePlan.objects.filter(person=self.user).count(), 10)

    def test_deleting_a_plan_makes_room(self):
        self.create("Last")
        self.plans[0].delete()
        self.assertEqual(self.create("Replacement").status_code, 201)

    def test_other_users_plans_dont_count(self):
        other = get_user_model().objects.create_user(username="o", password="x")
        DegreePlan.objects.create(name="Theirs", person=other)
        self.assertEqual(self.create("Last").status_code, 201)
