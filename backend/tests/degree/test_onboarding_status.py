from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import User
from degree.models import PDPBetaUser, PDPOnboardingStatus


class OnboardingStatusTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="top_secret")
        PDPBetaUser.objects.create(person=self.user)
        self.client = APIClient()
        self.client.force_login(self.user)
        self.url = reverse("onboarding-status")

    def test_not_onboarded_without_a_row(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"has_been_onboarded": False})
        self.assertFalse(PDPOnboardingStatus.objects.exists())

    def test_mark_onboarded(self):
        response = self.client.put(self.url, {"has_been_onboarded": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(self.url).data, {"has_been_onboarded": True})
        # Marking again updates the same row rather than adding one.
        self.client.put(self.url, {"has_been_onboarded": True}, format="json")
        self.assertEqual(PDPOnboardingStatus.objects.filter(person=self.user).count(), 1)

    def test_reset_onboarding(self):
        self.client.put(self.url, {"has_been_onboarded": True}, format="json")
        self.client.put(self.url, {"has_been_onboarded": False}, format="json")
        self.assertEqual(self.client.get(self.url).data, {"has_been_onboarded": False})

    def test_rejects_a_non_boolean(self):
        response = self.client.put(self.url, {"has_been_onboarded": "yes"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PDPOnboardingStatus.objects.exists())

    def test_requires_login(self):
        self.client.logout()
        self.assertIn(self.client.get(self.url).status_code, (401, 403))

    def test_requires_beta_access(self):
        PDPBetaUser.objects.filter(person=self.user).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Not in the PDP beta.")
