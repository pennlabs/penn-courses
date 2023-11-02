import json

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from tests.courses.util import create_mock_data, create_mock_recitation


class TestCourseSolver(TestCase):
    def setUp(self):
        self.s = ["CIS-1200", "CIS-1600", "MATH-1410", "OIDD-1010", "FNCE-1010", "WRIT-0760"]
        self.cis1200, self.cis1200_1 = create_mock_data(
            "CIS-1200-002", "2022C", start=1100, end=1200
        )
        _, self.cis1200_2 = create_mock_data("CIS-1200-002", "2022C", start=1300, end=1400)
        _, self.cis1200_213 = create_mock_recitation(
            "CIS-1200-213", "2022C", meeting_days="T", start=1515, end=1615
        )
        self.cis1600, self.cis1600_1 = create_mock_data(
            "CIS-1600-001", "2022C", meeting_days="T", start=1100, end=1200
        )
        _, self.cis1600_2 = create_mock_data(
            "CIS-1600-002", "2022C", meeting_days="T", start=1300, end=1400
        )
        self.cis1200.save()
        self.cis1200_1.save()
        self.cis1200_2.save()
        self.cis1200_213.save()
        self.cis1600.save()
        self.cis1600_1.save()
        self.cis1600_2.save()
        self.client = APIClient()

    def testScheduler(self):
        response = self.client.post(
            reverse("automatic-scheduler"),
            json.dumps(
                {
                    "courses": ["CIS-1200", "CIS-1600"],
                    "semester": "2022C",
                    "breaks": {"M": [], "T": [[10.59, 12.01]], "W": [], "R": [], "F": []},
                    "credit_limit": 5,
                }
            ),
            content_type="application/json",
        )
        json_data = response.json()
        with open(
            settings.BASE_DIR + "/tests/plan/course_solver_test_data/scheduler_data.json"
        ) as schedule_data:
            json_correct = json.load(schedule_data)
        self.assertEqual(json_data, json_correct)

    def testNOTFOUND(self):
        response = self.client.post(
            reverse("automatic-scheduler"),
            json.dumps(
                {
                    "courses": ["OIDD-1010"],
                    "semester": "2022C",
                    "breaks": {"M": [], "T": [[10.59, 12.01]], "W": [], "R": [], "F": []},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual([], response.json())
