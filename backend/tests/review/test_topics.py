from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Course, Instructor, Section, Topic
from tests.courses.util import create_mock_data, fill_course_soft_state
from tests.review.test_api import (
    PCRTestMixin,
    average_and_recent,
    create_review,
    rating,
    set_semester,
)


TEST_SEMESTER = "2017C"
assert TEST_SEMESTER > "2017A"


class CourseCodeChangedTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-471-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-371-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review(
            "CIS-471-001",
            "2017B",
            self.instructor_name,
            {"instructor_quality": 3},
        )
        create_review(
            "CIS-471-001",
            "2017A",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )

        Section.objects.all().update(activity="LEC")

        fill_course_soft_state()
        cis_371_2012A = Course.objects.get(full_code="CIS-371", semester="2012A")
        cis_471_2017A = Course.objects.get(full_code="CIS-471", semester="2017A")
        cis_471_2017A.parent_course = cis_371_2012A
        cis_471_2017A.manually_set_parent_course = True
        cis_471_2017A.save()
        fill_course_soft_state()

        self.extra_course_data = {
            "code": "CIS-471",
            "historical_codes": [
                {"full_code": "CIS-371", "branched_from": False, "semester": "2012A"}
            ],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-471",
            {
                "num_semesters": 3,
                **average_and_recent(3, 4),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_course_old_code(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-371",
            {
                "num_semesters": 3,
                **average_and_recent(3, 4),
                **self.extra_course_data,
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
            {
                **average_and_recent(3, 4),
                "courses": {"CIS-471": average_and_recent(3, 4)},
            },
        )

    def test_instructor_no_old_codes(self):
        res = self.client.get(
            reverse(
                "instructor-reviews",
                args=[Instructor.objects.get(name=self.instructor_name).pk],
            )
        )
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {
                "courses": {"CIS-471": average_and_recent(3, 4)},
            },
        )

    def test_department_no_old_codes(self):
        res = self.client.get(reverse("department-reviews", args=["CIS"]))
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-371", Instructor.objects.get(name=self.instructor_name).pk],
            {"sections": [rating(4), rating(3), rating(2)]},
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", Instructor.objects.get(name=self.instructor_name).pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "semester": TEST_SEMESTER,
                        "activity": "Lecture",
                        **rating(4),
                    },
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )


class CourseCodeChangedNoReviewTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

        _, section = create_mock_data("CIS-471-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name=self.instructor_name)
        section.instructors.add(instructor)

        create_review("CIS-371-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-471-001", "2017B", self.instructor_name, {"instructor_quality": 3})
        create_review(
            "CIS-471-001",
            "2017A",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        Section.objects.all().update(activity="LEC")

        fill_course_soft_state()
        cis_371_2012A = Course.objects.get(full_code="CIS-371", semester="2012A")
        cis_471_2017A = Course.objects.get(full_code="CIS-471", semester="2017A")
        cis_471_2017A.parent_course = cis_371_2012A
        cis_471_2017A.manually_set_parent_course = True
        cis_471_2017A.save()
        fill_course_soft_state()

        self.extra_course_data = {
            "code": "CIS-471",
            "historical_codes": [
                {"full_code": "CIS-371", "branched_from": False, "semester": "2012A"}
            ],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-471",
            {
                "num_semesters": 3,
                **average_and_recent(2.5, 3),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(2.5, 3),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_course_old_code(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-371",
            {
                "num_semesters": 3,
                **average_and_recent(2.5, 3),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(2.5, 3),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get(name=self.instructor_name).pk,
            {
                **average_and_recent(2.5, 3),
                "courses": {"CIS-471": average_and_recent(2.5, 3)},
            },
        )

    def test_instructor_no_old_codes(self):
        res = self.client.get(
            reverse(
                "instructor-reviews",
                args=[Instructor.objects.get(name=self.instructor_name).pk],
            )
        )
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {
                "courses": {"CIS-471": average_and_recent(2.5, 3)},
            },
        )

    def test_department_no_old_codes(self):
        res = self.client.get(reverse("department-reviews", args=["CIS"]))
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-371", Instructor.objects.get(name=self.instructor_name).pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "activity": "Lecture",
                        "semester": TEST_SEMESTER,
                        "forms_returned": None,
                        "forms_produced": None,
                    },
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", Instructor.objects.get(name=self.instructor_name).pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "activity": "Lecture",
                        "semester": TEST_SEMESTER,
                        "forms_returned": None,
                        "forms_produced": None,
                    },
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )


class InstructorNoReviewTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

        _, section = create_mock_data("CIS-471-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Instructor Two")
        section.instructors.add(instructor)

        create_review("CIS-371-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-471-001", "2017B", self.instructor_name, {"instructor_quality": 3})
        create_review(
            "CIS-471-001",
            "2017A",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        Section.objects.all().update(activity="LEC")

        fill_course_soft_state()
        cis_371_2012A = Course.objects.get(full_code="CIS-371", semester="2012A")
        cis_471_2017A = Course.objects.get(full_code="CIS-471", semester="2017A")
        cis_471_2017A.parent_course = cis_371_2012A
        cis_471_2017A.manually_set_parent_course = True
        cis_471_2017A.save()
        fill_course_soft_state()

        self.extra_course_data = {
            "code": "CIS-471",
            "historical_codes": [
                {"full_code": "CIS-371", "branched_from": False, "semester": "2012A"}
            ],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-471",
            {
                "num_semesters": 3,
                **average_and_recent(2.5, 3),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(2.5, 3),
                        "latest_semester": "2017B",
                    },
                    Instructor.objects.get(name="Instructor Two").pk: {
                        "average_reviews": {},
                        "recent_reviews": {},
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_course_old_code(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-371",
            {
                "num_semesters": 3,
                **average_and_recent(2.5, 3),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(2.5, 3),
                        "latest_semester": "2017B",
                    },
                    Instructor.objects.get(name="Instructor Two").pk: {
                        "average_reviews": {},
                        "recent_reviews": {},
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get(name=self.instructor_name).pk,
            {
                **average_and_recent(2.5, 3),
                "courses": {"CIS-471": average_and_recent(2.5, 3)},
            },
        )

    def test_instructor_no_old_codes(self):
        res = self.client.get(
            reverse(
                "instructor-reviews",
                args=[Instructor.objects.get(name=self.instructor_name).pk],
            )
        )
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {
                "courses": {"CIS-471": average_and_recent(2.5, 3)},
            },
        )

    def test_department_no_old_codes(self):
        res = self.client.get(reverse("department-reviews", args=["CIS"]))
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-371", Instructor.objects.get(name=self.instructor_name).pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", Instructor.objects.get(name=self.instructor_name).pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-371", Instructor.objects.get(name="Instructor Two").pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "activity": "Lecture",
                        "semester": TEST_SEMESTER,
                        "forms_returned": None,
                        "forms_produced": None,
                    },
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", Instructor.objects.get(name="Instructor Two").pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "activity": "Lecture",
                        "semester": TEST_SEMESTER,
                        "forms_returned": None,
                        "forms_produced": None,
                    },
                ]
            },
        )


class CourseCodeChangedTwoInstructorsMultipleSemestersTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2017A").save()
        AddDropPeriod(semester="2012A").save()
        AddDropPeriod(semester="2012C").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-471-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-471-001", "2017A", "Instructor Two", {"instructor_quality": 2})

        create_review("CIS-371-900", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-371-003", "2012C", "Instructor Two", {"instructor_quality": 1})

        Section.objects.all().update(activity="LEC")

        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor1_pk = self.instructor1.pk
        self.instructor2 = Instructor.objects.get(name="Instructor Two")
        self.instructor2_pk = self.instructor2.pk

        fill_course_soft_state()
        cis_371_2012A = Course.objects.get(full_code="CIS-371", semester="2012C")
        cis_471_2017A = Course.objects.get(full_code="CIS-471", semester="2017A")
        cis_471_2017A.parent_course = cis_371_2012A
        cis_471_2017A.manually_set_parent_course = True
        cis_471_2017A.save()
        fill_course_soft_state()

        self.extra_course_data = {
            "code": "CIS-471",
            "historical_codes": [
                {"full_code": "CIS-371", "branched_from": False, "semester": "2012C"}
            ],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-471",
            {
                "num_semesters": 4,
                **average_and_recent(2.25, 4),
                **self.extra_course_data,
                "instructors": {
                    self.instructor1_pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                    self.instructor2_pk: {
                        **average_and_recent(1.5, 2),
                        "latest_semester": "2017A",
                    },
                },
            },
        )

    def test_course_old_code(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-371",
            {
                "num_semesters": 4,
                **average_and_recent(2.25, 4),
                **self.extra_course_data,
                "instructors": {
                    self.instructor1_pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                    self.instructor2_pk: {
                        **average_and_recent(1.5, 2),
                        "latest_semester": "2017A",
                    },
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor1_pk,
            {
                **average_and_recent(3, 4),
                "courses": {
                    "CIS-471": {
                        **average_and_recent(3, 4),
                        "full_code": "CIS-471",
                        "code": "CIS-471",
                    }
                },
            },
        )
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2_pk,
            {
                **average_and_recent(1.5, 2),
                "courses": {
                    "CIS-471": {
                        **average_and_recent(1.5, 2),
                        "full_code": "CIS-471",
                        "code": "CIS-471",
                    }
                },
            },
        )

    def test_instructor_no_old_codes(self):
        res = self.client.get(reverse("instructor-reviews", args=[self.instructor1_pk]))
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {
                "courses": {"CIS-471": average_and_recent(2.25, 4)},
            },
        )

    def test_department_no_old_codes(self):
        res = self.client.get(reverse("department-reviews", args=["CIS"]))
        self.assertEqual(200, res.status_code)
        self.assertFalse("CIS-371" in res.data["courses"])

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", self.instructor1_pk],
            {
                "sections": [
                    {"course_code": "CIS-471", "activity": "Lecture", **rating(4)},
                    {"course_code": "CIS-371", "activity": "Lecture", **rating(2)},
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", self.instructor2_pk],
            {
                "sections": [
                    {"course_code": "CIS-471", "activity": "Lecture", **rating(2)},
                    {"course_code": "CIS-371", "activity": "Lecture", **rating(1)},
                ]
            },
        )


class BranchedFromTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "ARTH-2220-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review(
            "NELC-2055-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 3},
        )
        create_review("ARTH-222-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        topic_2220 = Topic.objects.get(most_recent__full_code="ARTH-2220")
        topic_2055 = Topic.objects.get(most_recent__full_code="NELC-2055")
        topic_222 = Topic.objects.get(most_recent__full_code="ARTH-222")
        topic_2220.branched_from = topic_222
        topic_2220.save()
        topic_2055.branched_from = topic_222
        topic_2055.save()

        self.extra_course_data_2220 = {
            "code": "ARTH-2220",
            "historical_codes": [
                {"full_code": "ARTH-222", "branched_from": True, "semester": "2012A"}
            ],
        }
        self.extra_course_data_2055 = {
            "code": "NELC-2055",
            "historical_codes": [
                {"full_code": "ARTH-222", "branched_from": True, "semester": "2012A"}
            ],
        }
        self.extra_course_data_222 = {
            "code": "ARTH-222",
            "historical_codes": [],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "ARTH-2220",
            {
                "num_semesters": 1,
                **average_and_recent(4, 4),
                **self.extra_course_data_2220,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(4, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )
        self.assertRequestContainsAppx(
            "course-reviews",
            "NELC-2055",
            {
                "num_semesters": 1,
                **average_and_recent(3, 3),
                **self.extra_course_data_2055,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 3),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )
        self.assertRequestContainsAppx(
            "course-reviews",
            "ARTH-222",
            {
                "num_semesters": 1,
                **average_and_recent(2, 2),
                **self.extra_course_data_222,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(2, 2),
                        "latest_semester": "2012A",
                    },
                },
            },
        )


class CourseOfferedInTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-471-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-371-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review(
            "CIS-471-001",
            "2017B",
            self.instructor_name,
            {"instructor_quality": 3},
        )
        create_review(
            "CIS-471-001",
            "2017A",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )

        Section.objects.all().update(activity="LEC")

        fill_course_soft_state()
        cis_371_2012A = Course.objects.get(full_code="CIS-371", semester="2012A")
        cis_471_2017A = Course.objects.get(full_code="CIS-471", semester="2017A")
        cis_471_2017A.parent_course = cis_371_2012A
        cis_471_2017A.manually_set_parent_course = True
        cis_471_2017A.save()
        fill_course_soft_state()

        self.extra_course_data = {
            "code": "CIS-471",
            "historical_codes": [
                {"full_code": "CIS-371", "branched_from": False, "semester": "2012A"}
            ],
        }

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-471",
            {
                "num_semesters": 3,
                **average_and_recent(3, 4),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
            query_params={"semester": "2017A"},
        )
        self.assertEqual(
            404,
            self.client.get(
                reverse("course-reviews", args=["CIS-471"]), {"semester": "2012A"}
            ).status_code,
        )

    def test_course_old_code(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-371",
            {
                "num_semesters": 3,
                **average_and_recent(3, 4),
                **self.extra_course_data,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
            query_params={"semester": "2012A"},
        )
        self.assertEqual(
            404,
            self.client.get(
                reverse("course-reviews", args=["CIS-371"]), {"semester": "2017A"}
            ).status_code,
        )

    def test_history(self):
        instructor = Instructor.objects.get(name=self.instructor_name)
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-371", instructor.pk],
            {"sections": [rating(4), rating(3), rating(2)]},
            query_params={"semester": "2012A"},
        )
        self.assertEqual(
            404,
            self.client.get(
                reverse("course-history", args=["CIS-371", instructor.pk]),
                {"semester": "2017A"},
            ).status_code,
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-471", instructor.pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-471",
                        "semester": TEST_SEMESTER,
                        "activity": "Lecture",
                        **rating(4),
                    },
                    {
                        "course_code": "CIS-471",
                        "semester": "2017B",
                        "activity": "Lecture",
                        **rating(3),
                    },
                    {
                        "course_code": "CIS-371",
                        "semester": "2012A",
                        "activity": "Lecture",
                        **rating(2),
                    },
                ]
            },
        )
        self.assertEqual(
            404,
            self.client.get(
                reverse("course-history", args=["CIS-471", instructor.pk]),
                {"semester": "2012A"},
            ).status_code,
        )
