import csv
import json
import os
from unittest.mock import patch

import numpy as np
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Course, Department, Section
from courses.util import invalidate_current_semester_cache
from plan.management.commands.recommendcourses import retrieve_course_clusters
from plan.management.commands.trainrecommender import (
    generate_course_vectors_dict,
    group_courses,
    train_recommender,
)
from plan.models import Schedule


TEST_SEMESTER = "2021C"
assert TEST_SEMESTER >= "2021C", "Some tests assume TEST_SEMESTER >= 2021C"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


User = get_user_model()


@patch("plan.views.retrieve_course_clusters")
class CourseRecommendationsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Creates departments, courses, sections and schedules from
        `/tests/plan/course_recs_test_data/course_data_test.csv`
        and `/tests/plan/course_recs_test_data/course_descriptions_test.csv`.

        The contents of `/tests/plan/course_recs_test_data/course_data_test.csv` are 3 columns:
        - a `person_id` (used when creating schedules)
        - a course `full_code` column (ie "PSCI-498")
        - a semester column (ranging between 2016C and 2020A).

        Courses are created with approximately the following specification:
        - `department_id`: Corresponds to the department code embedded in the `full_code`
        - `full_code` : corresponds to the course code column in
           `/tests/plan/course_recs_test_data/course_data_test.csv`
        - `semester` : corresponds to the semester column in
           `/tests/plan/course_recs_test_data/course_data_test.csv`. Additionally, if the value of
           the semester column in `/tests/plan/course_recs_test_data/course_data_test.csv`
           for a course is not "2020A" or "2017A" and the course `full_code` is not "HIST-650"
           another course entry is created with `semester` equal to `TEST_SEMESTER` as defined
           at the top of this file (2021C at the time of writing.)
        - `description` : corresponds to the entry in
           `/tests/plan/course_recs_test_data/course_descriptions_test.csv`

        Sections corresponding to each created course are created with approximately this
        specification
        - `code` : "001"
        - `full_code` : the course's `full_code` + "-001"
        """

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
                for course in courses_to_save:
                    course.save()
                    course_obs[course.full_code, course.semester] = course.id
            elif i == 2:
                Section.objects.bulk_create(sections_to_save)

        section_obs = dict()
        for section in Section.objects.all():
            section_obs[section.full_code, section.course.semester] = section.id
        cls.section_obs = section_obs

        schedules = dict()
        with open(course_data_path) as course_data_file:
            course_data_reader = csv.reader(course_data_file)
            for person_id, course_code, semester in course_data_reader:
                if person_id not in schedules:
                    schedules[person_id] = dict()
                if semester not in schedules[person_id]:
                    schedules[person_id][semester] = set()
                schedules[person_id][semester].add(course_code)

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
            + [
                User(
                    username=person_id,
                    email=person_id + "@example.com",
                    password=make_password(person_id + "_password"),
                    is_active=True,
                )
                for person_id in ["freshman", "gapsem", "noshow", "repeat"]
            ]
        )

        user_obs = dict()
        for user in User.objects.all():
            user_obs[user.username] = user.id

        # Create past schedules
        schedules_list = []
        for username in schedules.keys():
            for semester in schedules[username].keys():
                schedule = Schedule(
                    semester=semester,
                    name=username + " main schedule",
                )
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

    def subtest_with_edge_case_users(self):
        freshman = User.objects.get(username="freshman")
        freshman_client = APIClient()
        freshman_client.login(username="freshman", password="freshman_password")
        freshman_schedule = Schedule(
            person=freshman,
            semester=TEST_SEMESTER,
            name="Current schedule",
        )
        freshman_schedule.save()
        for course_code in ["GRMN-502", "GEOL-545", "MUSC-275"]:
            freshman_schedule.sections.add(self.section_obs[course_code + "-001", TEST_SEMESTER])
        response = freshman_client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

        gapsem = User.objects.get(username="gapsem")
        gapsem_client = APIClient()
        gapsem_client.login(username="gapsem", password="gapsem_password")
        gapsem_schedule = Schedule(
            person=gapsem,
            semester="2017A",
            name="Previous schedule",
        )
        gapsem_schedule.save()
        for course_code in ["LGIC-320", "ANTH-395", "NELC-337"]:
            gapsem_schedule.sections.add(self.section_obs[course_code + "-001", "2017A"])
        response = gapsem_client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

        noshow = User.objects.get(username="noshow")
        noshow_client = APIClient()
        noshow_client.login(username="noshow", password="noshow_password")
        noshow_schedule = Schedule(
            person=noshow,
            semester=TEST_SEMESTER,
            name="Empty schedule",
        )
        noshow_schedule.save()
        noshow_previous_schedule = Schedule(
            person=noshow,
            semester="2017C",
            name="Empty previous schedule",
        )
        noshow_previous_schedule.save()
        response = noshow_client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

        repeat = User.objects.get(username="repeat")
        repeat_client = APIClient()
        repeat_client.login(username="repeat", password="repeat_password")
        repeat_schedule_old = Schedule(
            person=repeat,
            semester="2016C",
            name="Old schedule",
        )
        repeat_schedule_old.save()
        for course_code in ["MUSC-275"]:
            repeat_schedule_old.sections.add(self.section_obs[course_code + "-001", "2016C"])
        repeat_schedule = Schedule(
            person=repeat,
            semester=TEST_SEMESTER,
            name="New schedule",
        )
        repeat_schedule.save()
        for course_code in ["GRMN-502", "GEOL-545", "MUSC-275"]:
            repeat_schedule.sections.add(self.section_obs[course_code + "-001", TEST_SEMESTER])
        response = repeat_client.post(reverse("recommend-courses"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data), 5)

    def test_with_edge_case_users(self, mock):
        mock.return_value = self.course_clusters
        self.subtest_with_edge_case_users()

    def test_with_edge_case_users_from_schedules(self, mock):
        mock.return_value = self.course_clusters_with_schedules
        self.subtest_with_edge_case_users()

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

    def test_retrieve_course_clusters_dev(self, mock):
        with patch.dict(
            "plan.management.commands.recommendcourses.os.environ",
            {"DJANGO_SETTINGS_MODULE": "PennCourses.settings.development"},
        ):
            clusters = retrieve_course_clusters()
        mock.return_value = clusters
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
