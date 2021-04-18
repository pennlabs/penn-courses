from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option
from rest_framework.test import APIClient

from alert.management.commands.recomputeESEs import recompute_percent_open
from alert.models import AddDropPeriod
from courses.models import Instructor, Section
from courses.util import get_add_drop_period, invalidate_current_semester_cache, record_update
from review.models import Review
from tests.review.test_api import PCRTestMixin, create_review


TEST_CURRENT_SEMESTER = "2021C"
TEST_SEMESTER = "2021A"  # Past semester for reviews

assert TEST_CURRENT_SEMESTER >= "2021C", "TEST_CURRENT_SEMESTER must be at least 2021C"
assert "b" not in TEST_CURRENT_SEMESTER.lower(), "TEST_CURRENT_SEMESTER cannot be a summer semester"
assert TEST_SEMESTER >= "2021A", "TEST_SEMESTER must be at least 2021A"
assert "b" not in TEST_SEMESTER.lower(), "TEST_SEMESTER cannot be a summer semester"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_CURRENT_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_CURRENT_SEMESTER).save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


"""
Below are some utility functions that make writing out the response.data dictionaries
a bit easier to do. All of the tests use instructor_quality as the reviewbit to test.
these helper functions cut down on a lot of the repeated characters in the responses.
"""


def ratings_dict(label, rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings):
    return {
        label: {
            "rInstructorQuality": rInstructorQuality,
            "rFinalEnrollmentPercentage": rFinalEnrollmentPercentage,
            "rPercentOpen": rPercentOpen,
            "rNumOpenings": rNumOpenings,
        }
    }


def average(rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings):
    return ratings_dict(
        "average_reviews",
        rInstructorQuality,
        rFinalEnrollmentPercentage,
        rPercentOpen,
        rNumOpenings,
    )


def recent(rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings):
    return ratings_dict(
        "recent_reviews", rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings
    )


def rating(rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings):
    return ratings_dict(
        "ratings", rInstructorQuality, rFinalEnrollmentPercentage, rPercentOpen, rNumOpenings
    )


class OneReviewExtraTestCase(TestCase, PCRTestMixin):
    @classmethod
    def setUpTestData(cls):
        set_semester()
        cls.instructor_name = "Instructor One"
        create_review(
            "ESE-120-001", TEST_SEMESTER, cls.instructor_name, {"instructor_quality": 3.5}
        )
        cls.ESE_120_001 = Section.objects.get(full_code="ESE-120-001")
        cls.ESE_120_001.capacity = 20
        cls.ESE_120_001.save()
        cls.instructor_quality = 3.5
        cls.adp = get_add_drop_period(TEST_SEMESTER)
        start = cls.adp.estimated_start
        end = cls.adp.estimated_end
        duration = end - start
        old_ESEus = "O"
        new_ESEus = "C"
        for date in [start + i * duration / 7 for i in range(1, 7)]:  # OCOCOCO
            record_update(
                "ESE-120-001", TEST_SEMESTER, old_ESEus, new_ESEus, False, dict(), created_at=date,
            )
            old_ESEus, new_ESEus = new_ESEus, old_ESEus
        recompute_percent_open(semesters=TEST_SEMESTER)
        cls.percent_open = (duration * 4 / 7).total_seconds() / duration.total_seconds()
        cls.num_updates = 3
        section = Section.objects.get()
        review = Review.objects.get()
        review.enrollment = 80
        section.capacity = 100
        review.save()
        section.save()
        cls.enrollment_pct = 80 / 100

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_course(self):
        subdict = {
            **average(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
            **recent(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
        }
        self.assertRequestContainsAppx(
            "course-reviews",
            "ESE-120",
            {**subdict, "instructors": {Instructor.objects.get().pk: subdict}},
        )

    def test_instructor(self):
        subdict = {
            **average(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
            **recent(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
        }
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get().pk,
            {**subdict, "courses": {"ESE-120": subdict}},
        )

    def test_department(self):
        subdict = {
            **average(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
            **recent(
                self.instructor_quality, self.enrollment_pct, self.percent_open, self.num_updates
            ),
        }
        self.assertRequestContainsAppx(
            "department-reviews", "ESE", {"courses": {"ESE-120": subdict}}
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["ESE-120", Instructor.objects.get().pk],
            {
                "sections": [
                    rating(
                        self.instructor_quality,
                        self.enrollment_pct,
                        self.percent_open,
                        self.num_updates,
                    )
                ]
            },
        )

    def test_autocomplete(self):
        self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "ESE",
                        "url": f"/instructor/{Instructor.objects.get().pk}",
                    }
                ],
                "courses": [{"title": "ESE-120", "desc": [""], "url": "/course/ESE-120",}],
                "departments": [{"title": "ESE", "desc": "", "url": "/department/ESE"}],
            },
        )


# TODO: below
"""
class TwoSemestersOneInstructorTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("ESE-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("ESE-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
            {
                "num_semesters": 2,
                **average_and_recent(3, 4),
                "instructors": {
                    Instructor.objects.get().pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContains(
            "instructor-reviews",
            Instructor.objects.get().pk,
            {**average_and_recent(3, 4), "courses": {"ESE-120": average_and_recent(3, 4)}},
        )

    def test_department(self):
        self.assertRequestContains(
            "department-reviews", "ESE", {"courses": {"ESE-120": average_and_recent(3, 4)}}
        )

    def test_history(self):
        self.assertRequestContains(
            "course-history",
            ["ESE-120", Instructor.objects.get().pk],
            {"sections": [rating(4), rating(2)]},
        )


class SemesterWithFutureCourseTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("ESE-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("ESE-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("ESE-160-001", "3008C", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
            {
                "num_semesters": 2,
                **average_and_recent(3, 4),
                "instructors": {
                    Instructor.objects.get().pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    }
                },
            },
        )

    def test_department(self):
        self.assertRequestContains(
            "department-reviews",
            "ESE",
            {"courses": {"ESE-120": average_and_recent(3, 4), "ESE-160": average_and_recent(2, 2)}},
        )


class TwoInstructorsOneSectionTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("ESE-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("ESE-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
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
        self.assertRequestContains(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"ESE-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContains(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"ESE-120": average_and_recent(2, 2)}},
        )


class TwoSectionTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("ESE-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("ESE-120-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
            {
                **average_and_recent(3, 3),
                "instructors": {
                    self.instructor1.pk: average_and_recent(4, 4),
                    self.instructor2.pk: average_and_recent(2, 2),
                },
            },
        )

    def test_instructor(self):
        self.assertRequestContains(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"ESE-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContains(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"ESE-120": average_and_recent(2, 2)}},
        )


class TwoInstructorsMultipleSemestersTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("ESE-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("ESE-120-001", "2017A", "Instructor Two", {"instructor_quality": 2})

        create_review("ESE-120-900", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("ESE-120-003", "2012C", "Instructor Two", {"instructor_quality": 1})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
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
        create_review("ESE-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 1})
        self.assertRequestContains(
            "course-reviews",
            "ESE-120",
            {
                **average_and_recent(2, 2.5),
                "instructors": {
                    self.instructor1.pk: {
                        **average_and_recent(3, 4),
                        "latest_semester": TEST_SEMESTER,
                    },
                    self.instructor2.pk: {
                        **average_and_recent(1.33, 1),
                        "latest_semester": TEST_SEMESTER,
                    },
                },
                "num_sections": 4,
                "num_sections_recent": 1,
            },
        )


class TwoDepartmentTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        create_review("ESE-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
        create_review("MATH-114-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        create_review("ENM-211-003", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 3})
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "MATH-114",
            {
                **average_and_recent(2, 2),
                "instructors": {self.instructor2.pk: average_and_recent(2, 2)},
            },
        )

    def test_instructor(self):
        self.assertRequestContains(
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
        set_semester()
        self.assertRequestContains(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": "Instructor One",
                        "desc": "ESE",
                        "url": f"/instructor/{self.instructor1.pk}",
                    },
                    {
                        "title": "Instructor Two",
                        "desc": "ENM,MATH",
                        "url": f"/instructor/{self.instructor2.pk}",
                    },
                ],
            },
        )


class NoReviewForSectionTestCase(TestCase, PCRTestMixinExtra):
    def setUp(self):
        create_review("ESE-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
        _, recitation, _, _ = get_or_create_course_and_section("ESE-120-201", TEST_SEMESTER)
        recitation.instructors.add(Instructor.objects.create(name="Instructor Two"))
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        res = self.assertRequestContains(
            "course-reviews",
            "ESE-120",
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
        self.assertEqual(404, self.client.get(reverse("course-reviews", args=["BLAH"])).ESEus_code)

    def test_instructor(self):
        self.assertEqual(404, self.client.get(reverse("instructor-reviews", args=[0])).ESEus_code)

    def test_department(self):
        self.assertEqual(
            404, self.client.get(reverse("department-reviews", args=["BLAH"])).ESEus_code
        )

    def test_history(self):
        self.assertEqual(
            404, self.client.get(reverse("course-history", args=["BLAH", 123])).ESEus_code
        )

    def test_no_reviews(self):
        get_or_create_course_and_section("ESE-120-001", TEST_SEMESTER)
        self.assertEqual(
            404, self.client.get(reverse("course-reviews", args=["ESE-120"])).ESEus_code
        )


class NoAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_course(self):
        self.assertEqual(403, self.client.get(reverse("course-reviews", args=["BLAH"])).ESEus_code)

    def test_instructor(self):
        self.assertEqual(403, self.client.get(reverse("instructor-reviews", args=[0])).ESEus_code)

    def test_department(self):
        self.assertEqual(
            403, self.client.get(reverse("department-reviews", args=["BLAH"])).ESEus_code
        )

    def test_history(self):
        self.assertEqual(
            403, self.client.get(reverse("course-history", args=["BLAH", 0])).ESEus_code
        )
"""
