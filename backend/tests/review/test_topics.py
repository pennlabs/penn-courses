from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Instructor
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
from review.import_utils.import_to_db import import_review
from review.test_api import (
    PCRTestMixin,
    average,
    average_and_recent,
    create_review,
    rating,
    ratings_dict,
    recent,
    set_semester,
)


TEST_SEMESTER = "2017C"
assert TEST_SEMESTER > "2012A"


class CodeChangeTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-1200-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4}
        )
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 2,
                **average_and_recent(3, 4),
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get(name=self.instructor_name).pk,
            {**average_and_recent(3, 4), "courses": {"CIS-120": average_and_recent(3, 4)}},
        )

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews", "CIS", {"courses": {"CIS-120": average_and_recent(3, 4)}}
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-120", Instructor.objects.get(name=self.instructor_name).pk],
            {"sections": [rating(4), rating(2)]},
        )


class SemesterWithFutureCourseTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        AddDropPeriod(semester="3008C").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        create_review("CIS-160-001", "3008C", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 2,
                **average_and_recent(3, 4),
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    }
                },
            },
        )

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {"courses": {"CIS-120": average_and_recent(3, 4), "CIS-160": average_and_recent(2, 2)}},
        )


class TwoInstructorsOneSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(3, 3),
                "instructors": {
                    self.instructor1.pk: average_and_recent(4, 4),
                    self.instructor2.pk: average_and_recent(2, 2),
                },
                "num_sections": 1,
                "num_sections_recent": 1,
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"CIS-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"CIS-120": average_and_recent(2, 2)}},
        )


class TwoSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(3, 3),
                "instructors": {
                    self.instructor1.pk: average_and_recent(4, 4),
                    self.instructor2.pk: average_and_recent(2, 2),
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"CIS-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"CIS-120": average_and_recent(2, 2)}},
        )


class TwoInstructorsMultipleSemestersTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2017A").save()
        AddDropPeriod(semester="2012A").save()
        AddDropPeriod(semester="2012C").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2017A", "Instructor Two", {"instructor_quality": 2})
        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )

        create_review("CIS-120-900", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-120-003", "2012C", "Instructor Two", {"instructor_quality": 1})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(2.25, 4),
                "instructors": {
                    self.instructor1.pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                    self.instructor2.pk: {**average_and_recent(1.5, 2), "latest_semester": "2017A"},
                },
            },
        )

    def test_course_with_cotaught_section(self):
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 1})
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(2, 2.5),
                "instructors": {
                    self.instructor1.pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                    self.instructor2.pk: {
                        **average_and_recent(4 / 3, 1),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
                "num_sections": 4,
                "num_sections_recent": 1,
            },
        )


class TwoDepartmentTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
        create_review(
            "CIS-120-002",
            "2007C",
            "Instructor One",
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        create_review("MATH-114-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        create_review("ENM-211-003", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 3})
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "MATH-114",
            {
                **average_and_recent(2, 2),
                "instructors": {self.instructor2.pk: average_and_recent(2, 2)},
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2.pk,
            {
                **average_and_recent(2.5, 2.5),
                "courses": {
                    "MATH-114": average_and_recent(2, 2),
                    "ENM-211": average_and_recent(3, 3),
                },
            },
        )

    def test_autocomplete(self):
        no_responses_instructor = Instructor.objects.get(name="No Responses Instructor")
        self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": "Instructor One",
                        "desc": "CIS",
                        "url": f"/instructor/{self.instructor1.pk}",
                    },
                    {
                        "title": "No Responses Instructor",
                        "desc": "CIS",
                        "url": f"/instructor/{no_responses_instructor.pk}",
                    },
                    {
                        "title": "Instructor Two",
                        "desc": "ENM,MATH",
                        "url": f"/instructor/{self.instructor2.pk}",
                    },
                ],
            },
        )


class NoReviewForSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
        create_review(
            "CIS-120-002",
            "2007C",
            "Instructor One",
            {"instructor_quality": 0},
            responses=0,
        )
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        _, recitation, _, _ = get_or_create_course_and_section("CIS-120-201", TEST_SEMESTER)
        recitation.instructors.add(Instructor.objects.create(name="Instructor Two"))
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(4, 4),
                "instructors": {self.instructor1.pk: average_and_recent(4, 4)},
            },
        )
        self.assertEqual(1, len(res["instructors"]))


class NotFoundTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_course(self):
        self.assertEqual(404, self.client.get(reverse("course-reviews", args=["BLAH"])).status_code)

    def test_instructor(self):
        self.assertEqual(404, self.client.get(reverse("instructor-reviews", args=[0])).status_code)

    def test_department(self):
        self.assertEqual(
            404, self.client.get(reverse("department-reviews", args=["BLAH"])).status_code
        )

    def test_history(self):
        self.assertEqual(
            404, self.client.get(reverse("course-history", args=["BLAH", 123])).status_code
        )

    def test_no_reviews(self):
        get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        self.assertEqual(
            404, self.client.get(reverse("course-reviews", args=["CIS-120"])).status_code
        )


class NoAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_course(self):
        self.assertEqual(403, self.client.get(reverse("course-reviews", args=["BLAH"])).status_code)

    def test_instructor(self):
        self.assertEqual(403, self.client.get(reverse("instructor-reviews", args=[0])).status_code)

    def test_department(self):
        self.assertEqual(
            403, self.client.get(reverse("department-reviews", args=["BLAH"])).status_code
        )

    def test_history(self):
        self.assertEqual(
            403, self.client.get(reverse("course-history", args=["BLAH", 0])).status_code
        )
