import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from degree.models import Degree, DegreePlan, Major, Minor, PDPBetaUser, Rule


User = get_user_model()


class MajorsAndMinorsApiTest(TestCase):
    """
    Majors and minors are added to a plan the same way degrees are, and are not filtered by
    school: an Engineering student may add the major part of a College degree.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="t", password="x", email="t@e.com")
        PDPBetaUser.objects.get_or_create(person=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="MEAM", concentration="GEN", year=2027
        )
        self.math = Major.objects.create(
            program_code="MATH-BA-GEN",
            code="MATH",
            name="Mathematics",
            concentration="GEN",
            year=2027,
            credits=13,
        )
        self.math.rules.add(
            Rule.objects.create(
                title="Calculus I and II",
                num=2,
                block_type="MAJOR",
                block_value="MATH",
                q="<Q: (AND: ('full_code__startswith', 'MATH'))>",
                share_targets=[{"kind": "MAJOR", "value": None}],
            )
        )
        self.minor = Minor.objects.create(
            program_code="CSCI-MINOR",
            code="CSCI",
            name="Computer Science",
            year=2027,
            credits=6,
        )

        self.plan = DegreePlan.objects.create(name="plan", person=self.user)
        self.plan.degrees.add(self.degree)

    def test_list_majors(self):
        response = self.client.get(reverse("major-list"))
        self.assertEqual(response.status_code, 200)
        codes = [major["program_code"] for major in response.data]
        self.assertIn("MATH-BA-GEN", codes)

    def test_list_minors(self):
        response = self.client.get(reverse("minor-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("CSCI-MINOR", [minor["program_code"] for minor in response.data])

    def test_major_detail_includes_rules(self):
        response = self.client.get(reverse("major-detail", args=[self.math.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([rule["title"] for rule in response.data["rules"]], ["Calculus I and II"])

    def test_add_and_remove_a_major(self):
        url = reverse("degreeplan-majors", args=[self.plan.id])
        response = self.client.post(
            url, json.dumps({"major_ids": [self.math.id]}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([major["id"] for major in response.data["majors"]], [self.math.id])
        self.assertEqual(list(self.plan.majors.all()), [self.math])

        response = self.client.delete(
            url, json.dumps({"major_ids": [self.math.id]}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.plan.majors.exists())

    def test_add_a_minor(self):
        response = self.client.post(
            reverse("degreeplan-minors", args=[self.plan.id]),
            json.dumps({"minor_ids": [self.minor.id]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([minor["id"] for minor in response.data["minors"]], [self.minor.id])

    def test_ids_must_be_a_list(self):
        response = self.client.post(
            reverse("degreeplan-majors", args=[self.plan.id]),
            json.dumps({"major_ids": self.math.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_a_plan_reports_all_three_kinds(self):
        self.plan.majors.add(self.math)
        self.plan.minors.add(self.minor)
        response = self.client.get(reverse("degreeplan-detail", args=[self.plan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["degrees"]), 1)
        self.assertEqual(len(response.data["majors"]), 1)
        self.assertEqual(len(response.data["minors"]), 1)
