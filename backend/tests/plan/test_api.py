import csv
import json
import os
from unittest.mock import patch

import numpy as np
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIClient

from courses.models import Course, Department, Instructor, Requirement, Section
from plan.management.commands.trainrecommender import (
    generate_course_vectors_dict,
    group_courses,
    train_recommender,
)
from plan.models import Schedule
from review.models import Review
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2021C"
assert TEST_SEMESTER >= "2021C", "Some tests assume TEST_SEMESTER >= 2021C"


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


@patch("plan.views.retrieve_course_clusters")
class CourseRecommendationsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
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

        departments_to_save = []
        department_obs = dict()
        courses_to_save = []
        course_obs = dict()
        sections_to_save = []

        def create_dont_save(course_code, semester, iter_num):
            dept_code = course_code.split("-")[0]
            if iter_num == 0:
                if dept_code not in department_obs:
                    dept = Department(code=dept_code, name=dept_code)
                    department_obs[dept_code] = dept
                    departments_to_save.append(dept)
            elif iter_num == 1:
                dept_id = department_obs[dept_code]
                course = Course(
                    code=course_code.split("-")[1],
                    semester=semester,
                    full_code=course_code,
                    description=test_descriptions[course_code],
                )
                course.department_id = dept_id
                courses_to_save.append(course)
            elif iter_num == 2:
                course_id = course_obs[course_code, semester]
                section = Section(
                    code="001",
                    full_code=course_code + "-001",
                    credits=1,
                    status="O",
                    activity="LEC",
                )
                section.course_id = course_id
                sections_to_save.append(section)

        curr_courses = set()
        for i in range(3):
            for course_code, semester in courses:
                assert semester != TEST_SEMESTER
                create_dont_save(course_code, semester, i)
            for course_code, semester in courses:
                curr_courses.add(course_code)
            for course_code, semester in courses:
                if semester in ["2017A", "2020A"] or course_code in ["HIST-650"]:
                    curr_courses.remove(course_code)
            for course_code in curr_courses:
                create_dont_save(course_code, TEST_SEMESTER, i)
            for extra_course_code in ["CIS-121", "CIS-262"]:
                create_dont_save(extra_course_code, TEST_SEMESTER, i)
            if i == 0:
                Department.objects.bulk_create(departments_to_save)
                department_obs = dict()
                for dept in Department.objects.all():
                    department_obs[dept.code] = dept.id
            elif i == 1:
                Course.objects.bulk_create(courses_to_save)
                for course in Course.objects.all():
                    course_obs[course.full_code, course.semester] = course.id
            elif i == 2:
                Section.objects.bulk_create(sections_to_save)

        section_obs = dict()
        for section in Section.objects.all():
            section_obs[section.full_code, section.course.semester] = section.id

        schedules = dict()
        with open(course_data_path) as course_data_file:
            course_data_reader = csv.reader(course_data_file)
            for person_id, course_code, semester in course_data_reader:
                if person_id not in schedules:
                    schedules[person_id] = dict()
                if semester not in schedules[person_id]:
                    schedules[person_id][semester] = set()
                schedules[person_id][semester].add(course_code)

        User = get_user_model()

        User.objects.bulk_create(
            [
                User(
                    username=person_id,
                    email=person_id + "@example.com",
                    password=make_password(person_id + "_password"),
                    is_active=True,
                )
                for person_id in schedules.keys()
            ]
        )

        user_obs = dict()
        for user in User.objects.all():
            user_obs[user.username] = user.id

        # Create past schedules
        schedules_list = []
        for username in schedules.keys():
            for semester in schedules[username].keys():
                schedule = Schedule(semester=semester, name=username + " main schedule",)
                schedule.person_id = user_obs[username]
                schedules_list.append(schedule)
        Schedule.objects.bulk_create(schedules_list)
        schedule_obs = dict()
        for schedule in Schedule.objects.all():
            schedule_obs[schedule.person_id, schedule.semester] = schedule
        for username in schedules.keys():
            for semester in schedules[username].keys():
                schedule = schedule_obs[user_obs[username], semester]
                for course_code in schedules[username][semester]:
                    if course_code in ["AFRC-437", "GRMN-180", "CIS-262"]:
                        continue
                    schedule.sections.add(section_obs[course_code + "-001", semester])

        schedule = Schedule(
            person=get_user_model().objects.get(username="hash1"),
            semester=TEST_SEMESTER,
            name="My Test Schedule",
        )
        schedule.save()
        for course_code in ["AFRC-437", "GRMN-180", "CIS-262"]:
            schedule.sections.add(section_obs[course_code + "-001", TEST_SEMESTER])

        cls.course_clusters = train_recommender(
            course_data_path=course_data_path, output_path=os.devnull
        )

        cls.course_clusters_with_schedules = train_recommender(
            course_data_path=None, output_path=os.devnull
        )

    def setUp(self):
        self.client = APIClient()
        self.client.login(username="hash1", password="hash1_password")
        set_semester()
        response = self.client.get(reverse("courses-list", args=[TEST_SEMESTER]))
        self.assertEqual(response.status_code, 200, response.content)
        self.course_objects = dict()
        for course_ob in response.data:
            self.course_objects[course_ob["id"]] = course_ob

    def subtest_with_user(self):
        response = self.client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_with_user(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_with_user()

    def test_with_user_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_with_user()

    def subtest_bad_data_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_bad_data_courses(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_bad_data_courses()

    def test_bad_data_courses_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_bad_data_courses()

    def subtest_bad_data_past(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_bad_data_past(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_bad_data_past()

    def test_bad_data_past_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_bad_data_past()

    def subtest_bad_data_past_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["CIS1233"], "curr_courses": ["CIS123123"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_bad_data_past_current(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_bad_data_past_current()

    def test_bad_data_past_current_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_bad_data_past_current()

    def check_response_data(self, data):
        for course_ob in data:
            should_be = self.course_objects[course_ob["id"]]
            should_be_str = (
                JSONRenderer().render(should_be, renderer_context={"indent": 4}).decode("UTF-8")
            )
            course_ob_str = (
                JSONRenderer().render(course_ob, renderer_context={"indent": 4}).decode("UTF-8")
            )
            error_msg = "\n\nresponse=" + course_ob_str + "\n\nshould be=" + should_be_str + "\n\n"
            self.assertEqual(should_be, course_ob, error_msg)

    def subtest_only_past_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"past_courses": ["BEPP-263", "GRMN-180"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.check_response_data(response.data)
        self.assertEqual(len(response.data), 5)

    def test_only_past_courses(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_only_past_courses()

    def test_only_past_courses_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_only_past_courses()

    def subtest_only_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps({"curr_courses": ["AFRC-437", "GRMN-180"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.check_response_data(response.data)
        self.assertEqual(len(response.data), 5)

    def test_only_current(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_only_current()

    def test_only_current_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_only_current()

    def subtest_past_and_current(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-262"],
                    "past_courses": ["ARTH-775", "EDUC-715"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.check_response_data(response.data)
        self.assertEqual(len(response.data), 5)

    def test_past_and_current(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_past_and_current()

    def test_past_and_current_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_past_and_current()

    def subtest_custom_num_recommendations(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-121"],
                    "past_courses": ["ARTH-775", "EDUC-715"],
                    "n_recommendations": 20,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.check_response_data(response.data)
        self.assertEqual(len(response.data), 20)

    def test_custom_num_recommendations(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_custom_num_recommendations()

    def test_custom_num_recommendations_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_custom_num_recommendations()

    def subtest_invalid_num_recommendations(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-121"],
                    "past_courses": ["ARTH-775", "EDUC-715"],
                    "n_recommendations": 0,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-121"],
                    "past_courses": ["ARTH-775", "EDUC-715"],
                    "n_recommendations": -1,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-121"],
                    "past_courses": ["ARTH-775", "EDUC-715"],
                    "n_recommendations": "test",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_invalid_num_recommendations(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_invalid_num_recommendations()

    def test_invalid_num_recommendations_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_invalid_num_recommendations()

    def subtest_non_current_course_in_curr_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "HIST-650"],
                    "past_courses": ["ARTH-775", "CIS-262"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_non_current_course_in_curr_courses(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_non_current_course_in_curr_courses()

    def test_non_current_course_in_curr_courses_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_non_current_course_in_curr_courses()

    def subtest_repeated_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "AFRC-437"],
                    "past_courses": ["ARTH-775", "CIS-262"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180"],
                    "past_courses": ["ARTH-775", "CIS-262", "CIS-262"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_repeated_courses(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_repeated_courses()

    def test_repeated_courses_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_repeated_courses()

    def subtest_overlapping_courses(self):
        response = self.client.post(
            reverse("recommend-courses"),
            json.dumps(
                {
                    "curr_courses": ["AFRC-437", "GRMN-180", "CIS-262"],
                    "past_courses": ["ARTH-775", "CIS-262"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_overlapping_courses(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_overlapping_courses()

    def test_overlapping_courses_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_overlapping_courses()

    def test_generate_course_vectors_dict_one_class_one_user_no_desc(self, mock):
        expected = (
            {"CIS-120": np.array([0.4472136, 0.89442719])},
            {"CIS-120": np.array([0.4472136, 0.89442719])},
        )
        actual = generate_course_vectors_dict([(0, "CIS-120", "2020A")], False)
        # self.assertEqual does not work with np arrays
        self.assertTrue(
            actual is not None and isinstance(actual[0], dict) and "CIS-120" in actual[0]
        )
        self.assertTrue(np.linalg.norm(actual[0]["CIS-120"] - expected[0]["CIS-120"]) < 1e-8)
        self.assertTrue(np.linalg.norm(actual[1]["CIS-120"] - expected[1]["CIS-120"]) < 1e-8)

    def test_group_courses_course_multiple_times_one_semester(self, mock):
        actual = group_courses([(0, "CIS-120", "2020A"), (0, "CIS-120", "2020A")])
        expected = {0: {"2020A": {"CIS-120": 2}}}
        self.assertEqual(expected, actual)

    def subtest_recommend_courses_command_user(self):
        call_command("recommendcourses", username="hash1", stdout=os.devnull)

    @patch("plan.management.commands.recommendcourses.retrieve_course_clusters")
    def test_recommend_courses_command_user(self, mock1, mock2):
        mock1.return_value = self.course_clusters
        mock2.return_value = self.course_clusters
        self.subtest_recommend_courses_command_user()

    @patch("plan.management.commands.recommendcourses.retrieve_course_clusters")
    def test_recommend_courses_command_user_from_schedules(self, mock1, mock2):
        mock1.return_value = self.course_clusters_with_schedules
        mock2.return_value = self.course_clusters_with_schedules
        self.subtest_recommend_courses_command_user()

    def subtest_recommend_courses_command_lists(self):
        call_command(
            "recommendcourses",
            curr_courses="AFRC-437,GRMN-180,CIS-262",
            past_courses="ARTH-775,EDUC-715",
            stdout=os.devnull,
        )

    @patch("plan.management.commands.recommendcourses.retrieve_course_clusters")
    def test_recommend_courses_command_lists(self, mock1, mock2):
        mock1.return_value = self.course_clusters
        mock2.return_value = self.course_clusters
        self.subtest_recommend_courses_command_lists()

    @patch("plan.management.commands.recommendcourses.retrieve_course_clusters")
    def test_recommend_courses_command_lists_from_schedules(self, mock1, mock2):
        mock1.return_value = self.course_clusters_with_schedules
        mock2.return_value = self.course_clusters_with_schedules
        self.subtest_recommend_courses_command_lists()
