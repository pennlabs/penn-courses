import json

from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient
from tests.courses.util import create_mock_data

from courses.models import Instructor, Requirement, User
from plan.models import Schedule
from review.models import Review


TEST_SEMESTER = "2019C"


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()


class CreditUnitFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        _, self.section2 = create_mock_data("CIS-120-201", TEST_SEMESTER)
        self.section.credits = 1.0
        self.section2.credits = 0.0
        self.section.save()
        self.section2.save()
        self.client = APIClient()
        set_semester()

    def test_include_course(self):
        response = self.client.get(reverse("courses-search", args=["current"]), {"cu": "1.0"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_include_multiple(self):
        response = self.client.get(reverse("courses-search", args=["current"]), {"cu": "0.5,1.0"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_exclude_course(self):
        response = self.client.get(reverse("courses-search", args=["current"]), {"cu": ".5,1.5"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


class RequirementFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.different_math, self.different_math1 = create_mock_data(
            "MATH-116-001", ("2019A" if TEST_SEMESTER == "2019C" else "2019C")
        )
        self.req = Requirement(semester=TEST_SEMESTER, code="REQ", school="SAS")
        self.req.save()
        self.req.courses.add(self.math)
        self.client = APIClient()
        set_semester()

    def test_return_all_courses(self):
        response = self.client.get(reverse("courses-search", args=["current"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_filter_for_req(self):
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"requirements": "REQ@SAS"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])

    def test_filter_for_req_dif_sem(self):
        req2 = Requirement(
            semester=("2019A" if TEST_SEMESTER == "2019C" else "2019C"), code="REQ", school="SAS"
        )
        req2.save()
        req2.courses.add(self.different_math)
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"requirements": "REQ@SAS"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])
        self.assertEqual(TEST_SEMESTER, response.data[0]["semester"])

    def test_multi_req(self):
        course3, section3 = create_mock_data("CIS-240-001", TEST_SEMESTER)
        req2 = Requirement(semester=TEST_SEMESTER, code="REQ2", school="SEAS")
        req2.save()
        req2.courses.add(course3)

        response = self.client.get(
            reverse("courses-search", args=["current"]), {"requirements": "REQ@SAS,REQ2@SEAS"}
        )
        self.assertEqual(0, len(response.data))

    def test_double_count_req(self):
        req2 = Requirement(semester=TEST_SEMESTER, code="REQ2", school="SEAS")
        req2.save()
        req2.courses.add(self.math)
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"requirements": "REQ@SAS,REQ2@SEAS"}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])


class CourseReviewAverageTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        _, self.section2 = create_mock_data("CIS-120-002", TEST_SEMESTER)
        self.instructor = Instructor(name="Person1")
        self.instructor.save()
        self.rev1 = Review(
            section=create_mock_data("CIS-120-003", "2005C")[1], instructor=self.instructor
        )
        self.rev1.save()
        self.rev1.set_averages(
            {"course_quality": 4, "instructor_quality": 4, "difficulty": 4,}
        )
        self.instructor2 = Instructor(name="Person2")
        self.instructor2.save()
        self.rev2 = Review(
            section=create_mock_data("CIS-120-002", "2015A")[1], instructor=self.instructor2
        )
        self.rev2.instructor = self.instructor2
        self.rev2.save()
        self.rev2.set_averages(
            {"course_quality": 2, "instructor_quality": 2, "difficulty": 2,}
        )

        self.section.instructors.add(self.instructor)
        self.section2.instructors.add(self.instructor2)
        self.client = APIClient()
        set_semester()

    def test_course_average(self):
        response = self.client.get(reverse("courses-detail", args=["current", "CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.data["course_quality"])
        self.assertEqual(3, response.data["instructor_quality"])
        self.assertEqual(3, response.data["difficulty"])

    def test_section_reviews(self):
        response = self.client.get(reverse("courses-detail", args=["current", "CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["sections"]))

    def test_section_no_duplicates(self):
        instructor3 = Instructor(name="person3")
        instructor3.save()
        rev3 = Review(section=self.rev2.section, instructor=instructor3)
        rev3.save()
        rev3.set_averages(
            {"course_quality": 1, "instructor_quality": 1, "difficulty": 1,}
        )
        self.section2.instructors.add(instructor3)
        response = self.client.get(reverse("courses-detail", args=["current", "CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["sections"]))
        self.assertEqual(
            1.5, response.data["sections"][1]["course_quality"], response.data["sections"][1]
        )

    def test_filter_courses_by_review_included(self):
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"difficulty": "2.5-3.5"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_filter_courses_by_review_excluded(self):
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"difficulty": "0-2"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


class CourseRecommendationsTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.s = Schedule(
            person=User.objects.create_user(
                username="jacob", email="jacob@example.com", password="top_secret"
            ),
            semester=TEST_SEMESTER,
            name="My Test Schedule",
        )
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")
        self.course, self.section = create_mock_data("CIS-121-001", TEST_SEMESTER)
        self.course, self.section = create_mock_data("CIS-262-001", TEST_SEMESTER)

    def test_with_user(self):
        response = self.client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)

    def test_bad_data_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_bad_data_past(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_bad_data_past_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"], "curr_courses": ["CIS123123"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_only_past_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS-121"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)

    def test_only_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["CIS-121"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)

    def test_past_and_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["CIS-121"], "past_courses": ["CIS-262"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
