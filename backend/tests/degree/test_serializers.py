from rest_framework.test import APIClient
from django.test import TestCase
from degree.models import DegreePlan, Rule


class SerializerTest(TestCase):
    def setUp(self):
        # Create sample DegreePlan instances
        self.degree_plan_1 = DegreePlan.objects.create(
            program="EU_BSE", degree="BSE", major="BIOL", year=2023
        )
        self.degree_plan_2 = DegreePlan.objects.create(
            program="EU_BSE", degree="BSE", major="CSCI", year=2024
        )

        # Create sample Rule instances related to degree plans
        self.rule_1 = Rule.objects.create(
            title="Rule 1",
            num_courses=4,
            credits=4.0,
            degree_plan=self.degree_plan_1,
            q="sample_q_1",
        )
        self.rule_2 = Rule.objects.create(
            title="Rule 2",
            num_courses=5,
            credits=5.0,
            degree_plan=self.degree_plan_1,
            q="sample_q_2",
        )
        self.rule_3 = Rule.objects.create(
            title="Rule 3",
            num_courses=3,
            credits=3.0,
            degree_plan=self.degree_plan_2,
            q="sample_q_3",
        )

    def test_degree_plan_serialization(self):
        client = APIClient()
        response = client.get(
            f"/api/degree-plan/{self.degree_plan_1.id}/"
        )  # Adjust the URL as needed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["program"], "EU_BSE")
        self.assertTrue(False)

    def test_rule_serialization(self):
        client = APIClient()
        response = client.get(f"/api/rule/{self.rule_1.id}/")  # Adjust the URL as needed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Rule 1")
