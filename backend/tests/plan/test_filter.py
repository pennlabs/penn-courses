import json

from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.management.commands.recompute_soft_state import recompute_precomputed_fields
from courses.models import Instructor, Section, User
from courses.util import invalidate_current_semester_cache, set_meetings
from plan.models import Schedule
from review.models import Review
from tests.courses.util import create_mock_async_class, create_mock_data


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


class CuFilterTestCase(TestCase):
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
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))


class DayFilterTestCase(TestCase):
    def setUp(self):
        _, self.cis_120_001 = create_mock_data("CIS-120-001", TEST_SEMESTER)  # days MWF

        _, self.cis_120_002 = create_mock_data(
            code="CIS-120-002", semester=TEST_SEMESTER, meeting_days="TR"
        )

        _, self.cis_160_001 = create_mock_data(
            code="CIS-160-001", semester=TEST_SEMESTER, meeting_days="TR"
        )

        _, self.cis_160_201 = create_mock_data(
            code="CIS-160-201", semester=TEST_SEMESTER, meeting_days="M"
        )
        self.cis_160_201.activity = "REC"
        self.cis_160_201.save()

        _, self.cis_160_202 = create_mock_data(
            code="CIS-160-202", semester=TEST_SEMESTER, meeting_days="W"
        )
        self.cis_160_202.activity = "REC"
        self.cis_160_202.save()

        _, self.cis_121_001 = create_mock_data(code="CIS-121-001", semester=TEST_SEMESTER)
        set_meetings(
            self.cis_121_001,
            [
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "MT",
                    "begin_time_24": 900,
                    "begin_time": "9:00 AM",
                    "end_time_24": 1000,
                    "end_time": "10:00 AM",
                },
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "WR",
                    "begin_time_24": 1330,
                    "begin_time": "1:30 PM",
                    "end_time_24": 1430,
                    "end_time": "2:30 PM",
                },
            ],
        )

        _, self.cis_262_001 = create_mock_async_class(code="CIS-262-001", semester=TEST_SEMESTER)

        recompute_precomputed_fields()

        self.all_codes = {"CIS-120", "CIS-160", "CIS-121", "CIS-262"}

        self.client = APIClient()
        set_semester()

    def test_only_async(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": [],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual({"CIS-262"}, {res["id"] for res in response.data})  # only async

    def test_all_days(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["M", "T", "W", "R", "F", "S", "U"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_illegal_characters(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["T", "R", "X", 2],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_lec_no_rec(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["T", "R"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_rec_no_lec(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["M", "W"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})

    def test_lec_and_rec(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["T", "W", "R"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-160", "CIS-120", "CIS-262"})

    def test_partial_match(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is",
                            "value": ["T"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})

    def test_contains_rec_no_sec(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is",
                            "value": ["W"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})

    def test_partial_multi_meeting_match(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["M", "W"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})

    def test_full_multi_meeting_match(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_any_of",
                            "value": ["M", "T", "W", "R"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
        self.assertEqual(
            {res["id"] for res in response.data},
            {"CIS-120", "CIS-121", "CIS-160", "CIS-262"},
        )

    def test_none_of(self):
        response = self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "days",
                            "op": "is_none_of",
                            "value": ["M", "W", "F"],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})


class IsOpenFilterTestCase(TestCase):
    def setUp(self):
        _, self.cis_160_001 = create_mock_data(
            code="CIS-160-001", semester=TEST_SEMESTER, meeting_days="TR"
        )

        _, self.cis_160_201 = create_mock_data(
            code="CIS-160-201", semester=TEST_SEMESTER, meeting_days="M"
        )
        self.cis_160_201.activity = "REC"
        self.cis_160_201.save()

        _, self.cis_160_202 = create_mock_data(
            code="CIS-160-202", semester=TEST_SEMESTER, meeting_days="W"
        )
        self.cis_160_202.activity = "REC"
        self.cis_160_202.save()

        def save_all():
            for section in [self.cis_160_001, self.cis_160_201, self.cis_160_202]:
                section.save()

        self.save_all = save_all
        self.all_codes = {"CIS-160"}
        self.non_open_statuses = [
            status[0] for status in Section.STATUS_CHOICES if status[0] not in ["O"]
        ]

        recompute_precomputed_fields()

        self.client = APIClient()
        set_semester()

    def _post_is_open(self):
        return self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "boolean",
                            "field": "is_open",
                            "value": True,
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

    def test_lec_open_all_rec_open(self):
        response = self._post_is_open()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_lec_open_one_rec_not_open(self):
        for status in self.non_open_statuses:
            self.cis_160_202.status = status
            self.save_all()

            response = self._post_is_open()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 1)
            self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_lec_open_all_rec_not_open(self):
        for status in self.non_open_statuses:
            self.cis_160_202.status = status
            self.cis_160_201.status = status
            self.save_all()

            response = self._post_is_open()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 0)
            self.assertEqual({res["id"] for res in response.data}, set())

    def test_rec_open_lec_not_open(self):
        for status in self.non_open_statuses:
            self.cis_160_001.status = status
            self.save_all()

            response = self._post_is_open()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 0)
            self.assertEqual({res["id"] for res in response.data}, set())

    def test_lec_not_open_all_rec_not_open(self):
        for status in self.non_open_statuses:
            self.cis_160_202.status = status
            self.cis_160_201.status = status
            self.cis_160_001.status = status
            self.save_all()

            response = self._post_is_open()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 0)
            self.assertEqual({res["id"] for res in response.data}, set())


class TimeFilterTestCase(TestCase):
    def setUp(self):
        _, self.cis_120_001 = create_mock_data("CIS-120-001", TEST_SEMESTER)  # time 11.0-12.0

        _, self.cis_120_002 = create_mock_data(
            code="CIS-120-002", semester=TEST_SEMESTER, start=1200, end=1330
        )

        _, self.cis_160_001 = create_mock_data(
            code="CIS-160-001", semester=TEST_SEMESTER, start=500, end=630
        )

        _, self.cis_160_201 = create_mock_data(
            code="CIS-160-201", semester=TEST_SEMESTER, start=1100, end=1200
        )
        self.cis_160_201.activity = "REC"
        self.cis_160_201.save()

        _, self.cis_160_202 = create_mock_data(
            code="CIS-160-202", semester=TEST_SEMESTER, start=1400, end=1500
        )
        self.cis_160_202.activity = "REC"
        self.cis_160_202.save()

        _, self.cis_121_001 = create_mock_data(code="CIS-121-001", semester=TEST_SEMESTER)
        set_meetings(
            self.cis_121_001,
            [
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "MT",
                    "begin_time_24": 900,
                    "begin_time": "9:00 AM",
                    "end_time_24": 1000,
                    "end_time": "10:00 AM",
                },
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "WR",
                    "begin_time_24": 1330,
                    "begin_time": "1:30 PM",
                    "end_time_24": 1430,
                    "end_time": "2:30 PM",
                },
            ],
        )

        _, self.cis_262_001 = create_mock_async_class(code="CIS-262-001", semester=TEST_SEMESTER)

        recompute_precomputed_fields()

        self.all_codes = {"CIS-120", "CIS-160", "CIS-121", "CIS-262"}

        self.client = APIClient()
        set_semester()

    def _post_time(self, start_time, end_time):
        children = []
        if start_time is not None:
            children.append(
                {
                    "type": "numeric",
                    "field": "start_time",
                    "op": "gte",
                    "value": start_time,
                }
            )
        if end_time is not None:
            children.append(
                {
                    "type": "numeric",
                    "field": "end_time",
                    "op": "lte",
                    "value": end_time,
                }
            )

        return self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": children,
                }
            ),
            content_type="application/json",
        )

    def test_whole_day(self):
        response = self._post_time(0, 23.59)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_crossover_times(self):
        response = self._post_time(15.0, 2.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})  # only async

    def test_start_end_same(self):

        response = self._post_time(5.5, 5.5)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})  # only async

    def test_lec_no_rec(self):
        response = self._post_time(4.59, 6.30)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})  # only async

    def test_one_match(self):
        response = self._post_time(11.30, 13.30)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_lec_and_rec(self):
        response = self._post_time(5.0, 12.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-160", "CIS-120", "CIS-262"})

    def test_contains_parts_of_two_sec(self):
        response = self._post_time(11.30, 13.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})

    def test_contains_rec_no_sec(self):
        response = self._post_time(11.30, 16.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_unbounded_right(self):
        response = self._post_time(11.30, None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_unbounded_left(self):
        response = self._post_time(None, 12.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-160", "CIS-262"})

    def test_multi_meeting_match(self):
        response = self._post_time(9.0, 15.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-121", "CIS-262"})


class ScheduleFilterTestCase(TestCase):
    def setUp(self):
        _, self.cis_120_001 = create_mock_data(
            "CIS-120-001", TEST_SEMESTER
        )  # time 11.0-12.0, days MWF

        _, self.cis_120_002 = create_mock_data(
            code="CIS-120-002",
            semester=TEST_SEMESTER,
            start=1200,
            end=1330,
            meeting_days="TR",
        )

        _, self.cis_160_001 = create_mock_data(
            code="CIS-160-001",
            semester=TEST_SEMESTER,
            start=500,
            end=630,
            meeting_days="TR",
        )

        _, self.cis_160_201 = create_mock_data(
            code="CIS-160-201",
            semester=TEST_SEMESTER,
            start=1100,
            end=1200,
            meeting_days="M",
        )
        self.cis_160_201.activity = "REC"
        self.cis_160_201.save()

        _, self.cis_160_202 = create_mock_data(
            code="CIS-160-202",
            semester=TEST_SEMESTER,
            start=1400,
            end=1500,
            meeting_days="W",
        )
        self.cis_160_202.activity = "REC"
        self.cis_160_202.save()

        _, self.cis_121_001 = create_mock_data(code="CIS-121-001", semester=TEST_SEMESTER)
        set_meetings(
            self.cis_121_001,
            [
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "MT",
                    "begin_time_24": 900,
                    "begin_time": "9:00 AM",
                    "end_time_24": 1000,
                    "end_time": "10:00 AM",
                },
                {
                    "building_code": "LLAB",
                    "room_code": "10",
                    "days": "WR",
                    "begin_time_24": 1330,
                    "begin_time": "1:30 PM",
                    "end_time_24": 1430,
                    "end_time": "2:30 PM",
                },
            ],
        )

        _, self.cis_262_001 = create_mock_async_class(code="CIS-262-001", semester=TEST_SEMESTER)

        recompute_precomputed_fields()

        self.all_codes = {"CIS-120", "CIS-160", "CIS-121", "CIS-262"}

        self.user = User.objects.create_user(
            username="jacob", email="jacob@example.com", password="top_secret"
        )

        self.empty_schedule = Schedule(
            person=self.user,
            semester=TEST_SEMESTER,
            name="Empty Schedule",
        )
        self.empty_schedule.save()

        self.all_available_schedule = Schedule(
            person=self.user,
            semester=TEST_SEMESTER,
            name="All Classes Available Schedule",
        )
        self.all_available_schedule.save()
        self.all_available_schedule.sections.set([self.cis_120_001])

        self.only_120_262_available_schedule = Schedule(
            person=self.user,
            semester=TEST_SEMESTER,
            name="Only CIS-120 and CIS-262 Available Schedule",
        )
        self.only_120_262_available_schedule.save()
        self.only_120_262_available_schedule.sections.set([self.cis_120_001, self.cis_121_001])

        self.only_262_available_schedule = Schedule(
            person=self.user,
            semester=TEST_SEMESTER,
            name="Only CIS-262 Available Schedule",
        )
        self.only_262_available_schedule.save()
        self.only_262_available_schedule.sections.set(
            [self.cis_120_001, self.cis_120_002, self.cis_121_001]
        )

        self.client = APIClient()
        set_semester()

    def _post_fit_schedule(self, schedule_id):
        return self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "value",
                            "field": "fit_schedule",
                            "value": str(schedule_id),
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

    def test_not_authenticated(self):
        response = self._post_fit_schedule(self.only_262_available_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_different_authenticated(self):
        User.objects.create_user(
            username="charley", email="charley@example.com", password="top_secret"
        )
        client2 = APIClient()
        client2.login(username="charley", password="top_secret")
        response = self._post_fit_schedule(self.only_262_available_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_invalid_schedule(self):
        self.client.login(username="jacob", password="top_secret")
        response = self._post_fit_schedule(-1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_empty_schedule(self):
        self.client.login(username="jacob", password="top_secret")
        response = self._post_fit_schedule(self.empty_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_all_available_schedule(self):
        self.client.login(username="jacob", password="top_secret")
        response = self._post_fit_schedule(self.all_available_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(self.all_codes))
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_only_120_262_available_schedule(self):
        self.client.login(username="jacob", password="top_secret")
        response = self._post_fit_schedule(self.only_120_262_available_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "CIS-262"})

    def test_only_262_available_schedule(self):
        self.client.login(username="jacob", password="top_secret")
        response = self._post_fit_schedule(self.only_262_available_schedule.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-262"})


class AttributeFilterTestCase(TestCase):
    def setUp(self):
        self.course1, self.section1 = create_mock_data(
            "CIS-120-001", TEST_SEMESTER, attributes=["EUNG", "NURS"]
        )
        self.course2, self.section2 = create_mock_data(
            "CIS-160-001", TEST_SEMESTER, attributes=["EUNG", "EUMA", "WUNM"]
        )

        self.client = APIClient()
        set_semester()

    def _post_attribute_filter(self, op, values):
        return self.client.post(
            reverse("courses-search", args=[TEST_SEMESTER]),
            data=json.dumps(
                {
                    "op": "AND",
                    "children": [
                        {
                            "type": "enum",
                            "field": "attribute",
                            "op": op,
                            "value": values,
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

    def test_attribute_included(self):
        response = self._post_attribute_filter("is_any_of", ["EUNG", "EUMA"])
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
