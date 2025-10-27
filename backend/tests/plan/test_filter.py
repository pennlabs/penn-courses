import json

from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Instructor
from review.models import Review
from courses.util import invalidate_current_semester_cache
from tests.courses.util import create_mock_data


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


class EnumFilterTestCase(TestCase):
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
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "enum",
                                "field": "cu",
                                "op": "is",
                                "value": ["1.0"],
                            }
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_include_multiple(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "enum",
                                "op": "is_any_of",
                                "field": "cu",
                                "value": ["0.5", "1.0"],
                            }
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_exclude_course(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "enum",
                                "op": "is_none_of",
                                "field": "cu",
                                "value": ["0.0", "1.0"],
                            }
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))

class NumericFilterTestCase(TestCase):
    def setUp(self):
        self.course1, self.section1 = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.instructor1 = Instructor(name="Person1")
        self.instructor1.save()
        self.rev1 = Review(
            section=create_mock_data("CIS-120-002", "2005C")[1],
            instructor=self.instructor1,
            responses=100,
        )
        self.rev1.save()
        self.rev1.set_averages(
            {
                "course_quality": 4,
                "instructor_quality": 4,
                "difficulty": 4,
            }
        )
        self.section1.instructors.add(self.instructor1)

        self.course2, self.section2 = create_mock_data("CIS-160-001", TEST_SEMESTER)
        self.instructor2 = Instructor(name="Person2")
        self.instructor2.save()
        self.rev2 = Review(
            section=create_mock_data("CIS-160-002", "2005C")[1],
            instructor=self.instructor2,
            responses=100,
        )
        self.rev2.save()
        self.rev2.set_averages(
            {
                "course_quality": 2,
                "instructor_quality": 2,
                "difficulty": 2,
            }
        )
        self.section2.instructors.add(self.instructor2)

        self.client = APIClient()
        set_semester()

    def test_lt_exclude(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "numeric",
                                "op": "lt",
                                "field": "difficulty",
                                "value": 2.0,
                            }
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))

    def test_gte_include(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "numeric",
                                "op": "gte",
                                "field": "course_quality",
                                "value": 2.0,
                            }
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_and(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "AND",
                        "children": [
                            {
                                "type": "numeric",
                                "op": "gt",
                                "field": "course_quality",
                                "value": 1.0,
                            },
                            {
                                "type": "numeric",
                                "op": "lt",
                                "field": "course_quality",
                                "value": 2.1,
                            },
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
    
    def test_or(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "filters": {
                        "type": "group",
                        "op": "OR",
                        "children": [
                            {
                                "type": "numeric",
                                "op": "gt",
                                "field": "course_quality",
                                "value": 3.0,
                            },
                            {
                                "type": "numeric",
                                "op": "lt",
                                "field": "difficulty",
                                "value": 3.0,
                            },
                        ],
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
