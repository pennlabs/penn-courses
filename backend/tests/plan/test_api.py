import csv
import json
import os
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from courses.models import Instructor, Requirement, User
from plan.management.commands.trainrecommender import train_recommender
from plan.models import Schedule
from review.models import Review
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2021C"


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
    @classmethod
    def setUpClass(cls):
        super(CourseRecommendationsTestCase, cls).setUpClass()
        course_data_path = (
            settings.BASE_DIR + "/tests/plan/course_recs_test_data/course_data_test.csv"
        )

        # Setting up test courses in the db
        test_descriptions = dict()
        with open(
            settings.BASE_DIR + "/tests/plan/course_recs_test_data/course_descriptions_test.csv"
        ) as course_desc_file:
            desc_reader = csv.reader(course_desc_file)
            for course, description in desc_reader:
                test_descriptions[course] = description
        courses = set()
        with open(course_data_path) as course_data_file:
            course_data_reader = csv.reader(course_data_file)
            for _, course_code, semester in course_data_reader:
                courses.add((course_code, semester))
        for course_code, semester in courses:
            course, _ = create_mock_data(course_code + "-001", semester)
            course.description = test_descriptions[course_code]
            course.save()
        for course_code, semester in courses:
            if semester not in ["2017A", "2020A"]:
                course, _ = create_mock_data(course_code + "-001", TEST_SEMESTER)
                course.description = test_descriptions[course_code]
                course.save()
        for extra_course_code in ["CIS-121", "CIS-262"]:
            course, _ = create_mock_data(extra_course_code + "-001", TEST_SEMESTER)
            course.description = test_descriptions[course_code]

        cls.course_clusters = train_recommender(
            course_data_path=course_data_path, output_path=os.devnull
        )

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

        patcher = patch("plan.views.retrieve_course_clusters", return_value=self.course_clusters)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_with_user(self):
        response = self.client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_bad_data_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_bad_data_past(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_bad_data_past_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"], "curr_courses": ["CIS123123"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_only_past_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["BEPP-263", "GRMN-180"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_only_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["AFRC-437", "GRMN-180"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_past_and_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-262"],
                    "past_courses": ["ARTH-775", "EDUC-715", "EDUC-715"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_custom_num_recommendations(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-121"],
                    "past_courses": ["ARTH-775", "EDUC-715", "EDUC-715", "CIS-120"],
                    "n_recommendations": 20,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 20)
