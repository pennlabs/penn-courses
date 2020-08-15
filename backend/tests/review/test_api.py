from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from courses.models import Instructor
from courses.util import get_or_create_course_and_section
from review.import_utils.import_to_db import import_review


TEST_SEMESTER = "2017C"


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()


def create_review(section_code, semester, instructor_name, bits):
    course, section, _, _ = get_or_create_course_and_section(section_code, semester)
    instructor, _ = Instructor.objects.get_or_create(name=instructor_name)
    section.instructors.add(instructor)
    import_review(section, instructor, None, None, None, bits, lambda x, y: None)


class PCRTestMixin(object):
    """
    This mixin class contains a utility function for quickly writing new tests.
    """

    def assertDictContains(self, entire, subdict, path=list()):
        """
        Assert that one dictionary is the subset of another.
        """
        if isinstance(entire, dict) and isinstance(subdict, dict):
            sublist = subdict.items()
        elif isinstance(entire, list) and isinstance(subdict, list):
            sublist = enumerate(subdict)
        else:
            return self.assertEqual(entire, subdict, "/".join(path))

        for k, v in sublist:
            self.assertDictContains(entire[k], subdict[k], path + [str(k)])

    def assertRequestContains(self, url, args, expected):
        """
        Do the equivalent of a "subset" check on the response from an API endpoint.
        :param url: `name` of django view
        :param args: single or multiple arguments for view.
        :param expected: expected values from view.
        """
        if not isinstance(args, list):
            args = [args]
        res = self.client.get(reverse(url, args=args))
        self.assertEqual(200, res.status_code)
        self.assertDictContains(res.data, expected)
        return res.data


"""
Below are some utility functions that make writing out the response.data dictionaries
a bit easier to do. All of the tests use instructor_quality as the reviewbit to test.
these helper functions cut down on a lot of the repeated characters in the responses.
"""


def ratings_dict(lbl, n):
    return {lbl: {"rInstructorQuality": n}}


def average(n):
    return ratings_dict("average_reviews", n)


def recent(n):
    return ratings_dict("recent_reviews", n)


def rating(n):
    return ratings_dict("ratings", n)


def average_and_recent(a, r):
    return {**average(a), **recent(r)}


class OneReviewTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(4, 4),
                "instructors": {Instructor.objects.get().pk: {**average_and_recent(4, 4)}},
            },
        )

    def test_instructor(self):
        self.assertRequestContains(
            "instructor-reviews",
            Instructor.objects.get().pk,
            {**average_and_recent(4, 4), "courses": {"CIS-120": {**average_and_recent(4, 4)}}},
        )

    def test_department(self):
        self.assertRequestContains(
            "department-reviews", "CIS", {"courses": {"CIS-120": average_and_recent(4, 4)}}
        )

    def test_history(self):
        self.assertRequestContains(
            "course-history", ["CIS-120", Instructor.objects.get().pk], {"sections": [rating(4)]}
        )

    def test_autocomplete(self):
        set_semester()
        self.assertRequestContains(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "CIS",
                        "url": f"/instructor/{Instructor.objects.get().pk}",
                    }
                ],
                "courses": [{"title": "CIS-120", "desc": [""], "url": "/course/CIS-120",}],
                "departments": [{"title": "CIS", "desc": "", "url": "/department/CIS"}],
            },
        )


class TwoSemestersOneInstructorTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "CIS-120",
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
            {**average_and_recent(3, 4), "courses": {"CIS-120": average_and_recent(3, 4)}},
        )

    def test_department(self):
        self.assertRequestContains(
            "department-reviews", "CIS", {"courses": {"CIS-120": average_and_recent(3, 4)}}
        )

    def test_history(self):
        self.assertRequestContains(
            "course-history",
            ["CIS-120", Instructor.objects.get().pk],
            {"sections": [rating(4), rating(2)]},
        )


class SemesterWithFutureCourseTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-160-001", "3008C", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        self.assertRequestContains(
            "course-reviews",
            "CIS-120",
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
            "CIS",
            {"courses": {"CIS-120": average_and_recent(3, 4), "CIS-160": average_and_recent(2, 2)}},
        )


class TwoInstructorsOneSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
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
        self.assertRequestContains(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"CIS-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContains(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"CIS-120": average_and_recent(2, 2)}},
        )


class TwoSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
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
        self.assertRequestContains(
            "instructor-reviews",
            self.instructor1.pk,
            {**average_and_recent(4, 4), "courses": {"CIS-120": average_and_recent(4, 4)}},
        )

        self.assertRequestContains(
            "instructor-reviews",
            self.instructor2.pk,
            {**average_and_recent(2, 2), "courses": {"CIS-120": average_and_recent(2, 2)}},
        )


class TwoInstructorsMultipleSemestersTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2017A", "Instructor Two", {"instructor_quality": 2})

        create_review("CIS-120-900", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-120-003", "2012C", "Instructor Two", {"instructor_quality": 1})
        self.instructor1 = Instructor.objects.get(name=self.instructor_name)
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        self.assertRequestContains(
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


class TwoDepartmentTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
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
                        "desc": "CIS",
                        "url": f"/instructor/{self.instructor1.pk}",
                    },
                    {
                        "title": "Instructor Two",
                        "desc": "ENM,MATH",
                        "url": f"/instructor/{self.instructor2.pk}",
                    },
                ],
                "courses": [{"title": "CIS-120", "desc": [""], "url": "/course/CIS-120"}],
                "departments": [{"title": "CIS", "desc": "", "url": "/department/CIS"}],
            },
        )


class NoReviewForSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor One", {"instructor_quality": 4})
        _, recitation, _, _ = get_or_create_course_and_section("CIS-120-201", TEST_SEMESTER)
        recitation.instructors.add(Instructor.objects.create(name="Instructor Two"))
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")

    def test_course(self):
        res = self.assertRequestContains(
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
