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
