from django.test import TestCase
from django.urls import reverse


class HealthTestCase(TestCase):
    def test_health(self):
        url = reverse("health")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"message": "OK"})
