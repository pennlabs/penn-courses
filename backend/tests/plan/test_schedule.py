import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework import status
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.util import get_average_reviews, invalidate_current_semester_cache
from PennCourses.settings.base import PATH_REGISTRATION_SCHEDULE_NAME
from plan.models import Break, Schedule
from tests.courses.util import create_mock_data_with_reviews


User = get_user_model()

TEST_SEMESTER = "2019C"
TEST_SEMESTER_PATH = "201930"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class ScheduleTest(TestCase):
    def setUp(self):
        set_semester()
        _, self.cis120, self.cis120_reviews = create_mock_data_with_reviews(
            "CIS-120-001", TEST_SEMESTER, 2
        )
        self.s = Schedule(
            person=User.objects.create_user(
                username="jacob", email="jacob@example.com", password="top_secret"
            ),
            semester=TEST_SEMESTER,
            name="My Test Schedule",
        )
        self.s.save()
        self.s.sections.set([self.cis120])
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")

    def check_serialized_section(self, serialized_section, section, reviews, consider_review_data):
        self.assertEqual(section.full_code, serialized_section.get("id"))
        self.assertEqual(section.status, serialized_section.get("status"))
        self.assertEqual(section.activity, serialized_section.get("activity"))
        self.assertEqual(section.credits, serialized_section.get("credits"))
        self.assertEqual(section.semester, serialized_section.get("semester"))

        if consider_review_data:
            fields = ["course_quality", "instructor_quality", "difficulty", "work_required"]
            for field in fields:
                expected = get_average_reviews(reviews, field)
                actual = serialized_section.get(field)
                self.assertAlmostEqual(expected, actual, 3)

    def test_semester_not_set(self):
        Option.objects.filter(key="SEMESTER").delete()
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(500, response.status_code)
        self.assertTrue("SEMESTER" in response.data["detail"])

    def test_get_schedule(self):
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "My Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 1)
        self.check_serialized_section(
            response.data[0]["sections"][0], self.cis120, self.cis120_reviews, True
        )

    def test_create_schedule(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_create_schedule_path_semesters(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER_PATH,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER_PATH},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER_PATH},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_create_schedule_no_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id + 1) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.check_serialized_section(response.data["sections"][0], cis121, cis121_reviews, True)
        self.check_serialized_section(response.data["sections"][1], cis160, cis160_reviews, True)

    def test_create_schedule_no_section_semesters(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "semester": TEST_SEMESTER,
                    "sections": [
                        {"id": "CIS-121-001"},
                        {"id": "CIS-160-001"},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id + 1) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.check_serialized_section(response.data["sections"][0], cis121, cis121_reviews, True)
        self.check_serialized_section(response.data["sections"][1], cis160, cis160_reviews, True)

    def test_create_schedule_default_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001"},
                        {"id": "CIS-160-001"},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id + 1) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.check_serialized_section(response.data["sections"][0], cis121, cis121_reviews, True)
        self.check_serialized_section(response.data["sections"][1], cis160, cis160_reviews, True)

    def test_update_schedule_no_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_no_section_semesters(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "semester": TEST_SEMESTER,
                    "sections": [
                        {"id": "CIS-121-001"},
                        {"id": "CIS-160-001"},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_default_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001"},
                        {"id": "CIS-160-001"},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_path_semesters(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "semester": TEST_SEMESTER_PATH,
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER_PATH},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_create_schedule_meetings(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "meetings": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_create_schedule_crns(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": cis121.crn, "semester": TEST_SEMESTER},
                        {"id": cis160.crn, "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_crns(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": cis121.crn, "semester": TEST_SEMESTER},
                        {"id": cis160.crn, "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_specific(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_specific_meetings(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "meetings": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEquals(sum([d["name"] == "New Test Schedule" for d in response.data]), 1)
        for d in response.data:
            if d["name"] == "New Test Schedule":
                sched = d
                break
        self.assertEqual(sched["semester"], TEST_SEMESTER)
        self.assertEqual(len(sched["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in sched["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in sched["sections"]]))
        for s in sched["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_specific_same_name(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "My Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "My Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "My Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data["sections"]]))
        for s in response.data["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_general(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "id": str(self.s.id),
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 2)
        self.assertEquals(1, sum([s["id"] == "CIS-121-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-121-001":
                section_cis121 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis121, cis121, cis121_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_update_schedule_general_same_name(self):
        _, cis160, cis160_reviews = create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "id": str(self.s.id),
                    "semester": TEST_SEMESTER,
                    "name": "My Test Schedule",
                    "sections": [
                        {"id": "CIS-120-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "My Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(2, len(response.data[0]["sections"]))
        self.assertEquals(1, sum([s["id"] == "CIS-120-001" for s in response.data[0]["sections"]]))
        self.assertEquals(1, sum([s["id"] == "CIS-160-001" for s in response.data[0]["sections"]]))
        for s in response.data[0]["sections"]:
            if s["id"] == "CIS-120-001":
                section_cis120 = s
            if s["id"] == "CIS-160-001":
                section_cis160 = s
        self.check_serialized_section(section_cis120, self.cis120, self.cis120_reviews, True)
        self.check_serialized_section(section_cis160, cis160, cis160_reviews, True)

    def test_delete(self):
        response = self.client.delete("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(response.status_code, 204)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))

    def test_semesters_not_uniform(self):
        create_mock_data_with_reviews("CIS-121-001", "1739C", 2)
        create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": "1739C"},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("semester", response.data["detail"])

    def test_semesters_not_uniform_update(self):
        create_mock_data_with_reviews("CIS-121-001", "1739C", 2)
        create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "id": str(self.s.id),
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": "1739C"},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("semester", response.data["detail"])

    def test_schedule_dne(self):
        response = self.client.get("/api/plan/schedules/1000/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"].code, "not_found")

    def test_name_already_exists(self):
        create_mock_data_with_reviews("CIS-121-001", TEST_SEMESTER, 2)
        create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "My Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)

    def test_section_dne_one(self):
        create_mock_data_with_reviews("CIS-160-001", TEST_SEMESTER, 2)
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "One or more sections not found in database.")

    def test_section_dne_all(self):
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "One or more sections not found in database.")

    def test_user_not_logged_in(self):
        client2 = APIClient()
        response = client2.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)
        response = client2.get("/api/plan/schedules/")
        self.assertEqual(403, response.status_code)
        response = client2.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "meetings": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)

    def test_user_cant_access_other_users_schedule(self):
        User.objects.create_user(
            username="charley", email="charley@example.com", password="top_secret"
        )
        client2 = APIClient()
        client2.login(username="charley", password="top_secret")
        response = client2.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "id": str(self.s.id),
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)
        response = client2.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": "New Test Schedule",
                    "meetings": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)
        response = client2.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))

    def test_create_schedule_no_semester_no_courses(self):
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps({"name": "New Test Schedule", "sections": []}),
            content_type="application/json",
        )
        self.assertEqual(201, response.status_code)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[1]["name"], "New Test Schedule")
        self.assertEqual(response.data[1]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[1]["sections"]), 0)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id + 1) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data["sections"]), 0)

    def test_update_schedule_no_semester_no_courses(self):
        response = self.client.put(
            "/api/plan/schedules/" + str(self.s.id) + "/",
            json.dumps({"name": "New Test Schedule", "sections": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["name"], "New Test Schedule")
        self.assertEqual(response.data[0]["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]["sections"]), 0)
        response = self.client.get("/api/plan/schedules/" + str(self.s.id) + "/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["name"], "New Test Schedule")
        self.assertEqual(response.data["semester"], TEST_SEMESTER)
        self.assertEqual(len(response.data["sections"]), 0)

    def test_create_path_registration_schedule_403(self):
        response = self.client.post(
            "/api/plan/schedules/",
            json.dumps(
                {
                    "semester": TEST_SEMESTER,
                    "name": PATH_REGISTRATION_SCHEDULE_NAME,
                    "sections": [
                        {"id": "CIS-121-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-160-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "You cannot create/update/delete a schedule with the name "
            + PATH_REGISTRATION_SCHEDULE_NAME,
        )

    def test_update_to_path_registration_schedule_403(self):
        response = self.client.put(
            f"/api/plan/schedules/{self.s.id}/",
            json.dumps({"name": PATH_REGISTRATION_SCHEDULE_NAME, "sections": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "You cannot create/update/delete a schedule with the name "
            + PATH_REGISTRATION_SCHEDULE_NAME,
        )

    def test_update_from_path_registration_schedule_403(self):
        path_schedule = Schedule.objects.create(
            name=PATH_REGISTRATION_SCHEDULE_NAME, person=self.s.person, semester=TEST_SEMESTER
        )
        response = self.client.put(
            f"/api/plan/schedules/{path_schedule.id}/",
            json.dumps({"name": "Not Path Registration", "sections": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "You cannot create/update/delete a schedule with the name "
            + PATH_REGISTRATION_SCHEDULE_NAME,
        )

    def test_delete_path_registration_schedule_403(self):
        path_schedule = Schedule.objects.create(
            name=PATH_REGISTRATION_SCHEDULE_NAME, person=self.s.person, semester=TEST_SEMESTER
        )
        response = self.client.delete(f"/api/plan/schedules/{path_schedule.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "You cannot create/update/delete a schedule with the name "
            + PATH_REGISTRATION_SCHEDULE_NAME,
        )

    def platform_introspect_response(self):
        # Build a response from platform's introspect route
        # (for mocking platform IPC auth for Path Registration schedule updating)
        return {
            "exp": 1123,
            "user": {
                "pennid": self.s.person.id,
                "first_name": "first",
                "last_name": "last",
                "username": "abc",
                "email": "test@test.com",
                "affiliation": [],
                "user_permissions": [],
                "groups": ["student", "member"],
                "token": {
                    "access_token": "abc",
                    "refresh_token": "123",
                    "expires_in": 100,
                },
            },
        }

    @patch("accounts.authentication.requests.post")
    def test_update_from_path_nonexistent_schedule(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json = self.platform_introspect_response
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        response = APIClient(enforce_csrf_checks=True).put(
            "/api/plan/schedules/path/",
            json.dumps(
                {
                    "name": PATH_REGISTRATION_SCHEDULE_NAME,
                    "sections": [{"id": "CIS-120-001", "semester": TEST_SEMESTER}],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer abc",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            sum([d["name"] == PATH_REGISTRATION_SCHEDULE_NAME for d in response.data]), 1
        )
        for schedule in response.data:
            if schedule["name"] == PATH_REGISTRATION_SCHEDULE_NAME:
                path_schedule = schedule
        self.assertEqual(len(path_schedule["sections"]), 1)
        self.assertEqual(path_schedule["sections"][0]["id"], "CIS-120-001")

    @patch("accounts.authentication.requests.post")
    def test_update_from_path(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json = self.platform_introspect_response
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        Schedule.objects.create(
            name=PATH_REGISTRATION_SCHEDULE_NAME, person=self.s.person, semester=TEST_SEMESTER
        )
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        response = APIClient(enforce_csrf_checks=True).put(
            "/api/plan/schedules/path/",
            json.dumps(
                {
                    "name": PATH_REGISTRATION_SCHEDULE_NAME,
                    "sections": [{"id": "CIS-120-001", "semester": TEST_SEMESTER}],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer abc",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            sum([d["name"] == PATH_REGISTRATION_SCHEDULE_NAME for d in response.data]), 1
        )
        for schedule in response.data:
            if schedule["name"] == PATH_REGISTRATION_SCHEDULE_NAME:
                path_schedule = schedule
        self.assertEqual(len(path_schedule["sections"]), 1)
        self.assertEqual(path_schedule["sections"][0]["id"], "CIS-120-001")

    @patch("accounts.authentication.requests.post")
    def test_update_from_path_nonexistent_sections(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json = self.platform_introspect_response
        Schedule.objects.create(
            name=PATH_REGISTRATION_SCHEDULE_NAME, person=self.s.person, semester=TEST_SEMESTER
        )
        response = APIClient(enforce_csrf_checks=True).put(
            "/api/plan/schedules/path/",
            json.dumps(
                {
                    "name": PATH_REGISTRATION_SCHEDULE_NAME,
                    "sections": [
                        {"id": "FAKE-120-001", "semester": TEST_SEMESTER},
                        {"id": "CIS-120-001", "semester": TEST_SEMESTER},
                        {"id": "FAKE-1200-001", "semester": TEST_SEMESTER},
                    ],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer abc",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/api/plan/schedules/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            sum([d["name"] == PATH_REGISTRATION_SCHEDULE_NAME for d in response.data]), 1
        )
        for schedule in response.data:
            if schedule["name"] == PATH_REGISTRATION_SCHEDULE_NAME:
                path_schedule = schedule
        self.assertEqual(len(path_schedule["sections"]), 1)
        self.assertEqual(path_schedule["sections"][0]["id"], "CIS-120-001")


class BreakViewSetTests(TestCase):
    def setUp(self):
        # Create and authenticate a test user
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client = APIClient()
        self.client.login(username="testuser", password="testpassword")

        # Create an initial Break instance to test update operations
        self.break_obj = Break.objects.create(
            person=self.user, name="Morning Break", location_string="Cafeteria"
        )
        self.break_obj.save()

        # Use Django's reverse to dynamically get the correct endpoint
        self.break_list_url = reverse("breaks-list")  # /api/plan/breaks/
        self.break_detail_url = reverse(
            "breaks-detail", kwargs={"pk": self.break_obj.id}
        )  # /api/plan/breaks/{id}/

    @patch("plan.views.set_meetings")
    def test_create_break(self, mock_set_meetings):
        """
        Ensure that posting a new break (without an "id") creates the break
        and returns a 201 response.
        """
        data = {
            "id": 2,
            "name": "Afternoon Break",
            "location_string": "Lobby",
            "meetings": [],  # No meetings provided
        }
        response = self.client.post(self.break_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that a new Break was created with the proper fields.
        new_break_id = response.data.get("id")
        self.assertIsNotNone(new_break_id)
        new_break = Break.objects.get(id=new_break_id)
        self.assertEqual(new_break.name, "Afternoon Break")
        self.assertEqual(new_break.location_string, "Lobby")

        # Verify that set_meetings was called with the new break and meetings list.
        mock_set_meetings.assert_called_once_with(new_break, [])
        self.assertEqual(response.data.get("message"), "success")

    @patch("plan.views.set_meetings")
    def test_update_break_existing(self, mock_set_meetings):
        """
        If a break with the provided "id" exists, sending a POST
        request with that id should update it.
        """
        data = {
            "id": self.break_obj.id,
            "name": "Updated Break",
            "location_string": "New Location",
            "meetings": [
                {
                    "days": "MT",
                    "begin_time_24": 900,
                    "begin_time": "9:00 AM",
                    "end_time_24": 1000,
                    "end_time": "10:00 AM",
                },
            ],
        }
        response = self.client.post(self.break_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh the object from the database to confirm changes.
        self.break_obj.refresh_from_db()
        self.assertEqual(self.break_obj.name, "Updated Break")
        self.assertEqual(self.break_obj.location_string, "New Location")

        self.assertEqual(response.data.get("message"), "success")
        self.assertEqual(response.data.get("id"), self.break_obj.id)

    def test_update_break_nonexistent(self):
        """
        Posting a break update with an id that does not exist should create a break  with that ID.
        """
        data = {
            "id": 9999,  # An id that does not exist for this user
            "name": "Nonexistent Break",
            "location_string": "Nowhere",
            "meetings": [],
        }
        response = self.client.post(self.break_list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get("message"), "success")

        new_break = Break.objects.get(id=response.data.get("id"))

        self.assertEqual(new_break.name, "Nonexistent Break")
        self.assertEqual(new_break.location_string, "Nowhere")

    def test_list_breaks(self):
        """
        Ensure that a GET request to the break-list endpoint returns the list
        of breaks for the authenticated user.
        """
        response = self.client.get(self.break_list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that our initial break ("Morning Break") is in the returned list.
        break_names = [item.get("name") for item in response.data]
        self.assertIn("Morning Break", break_names)

    def test_get_break_by_id(self):
        """
        Ensure that retrieving a specific break by its id works.
        """
        response = self.client.get(self.break_detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.break_obj.name)
        self.assertEqual(response.data["location_string"], self.break_obj.location_string)

    def test_delete_break(self):
        """
        Ensure that deleting a break works.
        """
        response = self.client.delete(self.break_detail_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Break.objects.filter(id=self.break_obj.id).exists())
