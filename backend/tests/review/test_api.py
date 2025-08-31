from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Course, Instructor, PreNGSSRestriction, Section, StatusUpdate
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
from review.import_utils.import_to_db import import_review
from review.models import Review
from tests.courses.util import create_mock_data, fill_course_soft_state


TEST_SEMESTER = "2022C"
assert TEST_SEMESTER > "2012A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


def create_review(section_code, semester, instructor_name, bits, responses=100):
    course, section, _, _ = get_or_create_course_and_section(section_code, semester)
    instructor, _ = Instructor.objects.get_or_create(name=instructor_name)
    section.instructors.add(instructor)
    import_review(section, instructor, None, responses, None, bits, lambda x, y=None: None)
    fill_course_soft_state()


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

    def assertRequestContainsAppx(self, url, args, expected, query_params={}):
        """
        Do the equivalent of a "subset" check on the response from an API endpoint.
        :param url: `name` of django view
        :param args: single or multiple arguments for view.
        :param expected: expected values from view.
        :param query_params: query parameters to be included in request, defaults to empty dict.
        """
        if not isinstance(args, list):
            args = [args]
        res = self.client.get(f"{reverse(url, args=args)}?{urlencode(query_params)}")
        self.assertEqual(200, res.status_code)
        self.assertDictContainsAppx(
            res.data,
            expected,
            extra_error_str="\nresponse:" + str(res.json()) + "\n\nexpected:" + str(expected),
        )
        return res.data

    def assertDictAlmostEquals(self, actual, expected, path=None, extra_error_str=""):
        """
        Assert that one dictionary almost equals another (allowing small deviations for floats)
        """
        path = path if path is not None else []
        if isinstance(actual, dict) and isinstance(expected, dict):
            self.assertEquals(
                actual.keys(),
                expected.keys(),
                "Dict path" + "/".join(path) + "\n" + extra_error_str,
            )
            for key in actual:
                self.assertDictAlmostEquals(actual[key], expected[key], path + [str(key)])
        try:
            actual_float = float(actual)
            expected_float = float(expected)
            self.assertAlmostEquals(
                actual_float,
                expected_float,
                msg="Dict path: " + "/".join(path) + "\n" + extra_error_str,
            )
        except (TypeError, ValueError):
            self.assertEquals(
                actual,
                expected,
                "Dict path: " + "/".join(path) + "\n" + extra_error_str,
            )

    def assertDictContainsAppx(self, entire, subdict, path=None, extra_error_str=""):
        """
        Assert that one dictionary is the subset of another.
        """
        path = path if path is not None else []
        if (isinstance(entire, list) and isinstance(subdict, list)) or (
            isinstance(entire, tuple) and isinstance(subdict, tuple)
        ):
            entire = dict(enumerate(entire))
            subdict = dict(enumerate(subdict))
        elif not (isinstance(entire, dict) and isinstance(subdict, dict)):
            return self.assertDictAlmostEquals(
                entire, subdict, path, extra_error_str=extra_error_str
            )
        for k, v in subdict.items():
            self.assertTrue(
                k in entire.keys(),
                f"{k} not in keys of {entire}, but should be. "
                + "\nDict path: "
                + "/".join(path)
                + "\n"
                + extra_error_str,
            )
            self.assertDictContainsAppx(entire[k], subdict[k], path + [str(k)], extra_error_str)


"""
Below are some utility functions that make writing out the response.data dictionaries
a bit easier to do. All of the tests use instructor_quality as the reviewbit to test.
these helper functions cut down on a lot of the repeated characters in the responses.
"""


def ratings_dict(label, n):
    return {label: {"rInstructorQuality": n}}


def average(n):
    return ratings_dict("average_reviews", n)


def recent(n):
    return ratings_dict("recent_reviews", n)


def rating(n):
    return ratings_dict("ratings", n)


def average_and_recent(a, r):
    return {**average(a), **recent(r)}


def no_reviews_avg_recent(num_semesters, recent_semester):
    return {
        "average_reviews": {
            "rSemesterCount": num_semesters,
            "rSemesterCalc": recent_semester,
        },
        "recent_reviews": {"rSemesterCount": 0},
    }


class TestHasReview(TestCase):
    def test_has_none(self):
        _, section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Rajiv Gandhi")
        section.instructors.add(instructor)
        fill_course_soft_state()
        self.assertFalse(Section.objects.get(id=section.id).has_reviews)

    def test_has_no_responses(self):
        _, section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Rajiv Gandhi")
        section.instructors.add(instructor)
        import_review(
            section,
            instructor,
            None,
            1,
            None,
            {"instructor_quality": 4},
            lambda x, y=None: None,
        )
        fill_course_soft_state()
        self.assertTrue(Section.objects.get(id=section.id).has_reviews)

    def test_has_review_with_no_responses(self):
        _, section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Rajiv Gandhi")
        section.instructors.add(instructor)
        import_review(
            section,
            instructor,
            None,
            0,
            None,
            {"instructor_quality": 4},
            lambda x, y=None: None,
        )
        fill_course_soft_state()
        self.assertFalse(Section.objects.get(id=section.id).has_reviews)

    def test_has_one(self):
        _, section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Rajiv Gandhi")
        section.instructors.add(instructor)
        import_review(
            section,
            instructor,
            None,
            10,
            None,
            {"instructor_quality": 4},
            lambda x, y=None: None,
        )
        fill_course_soft_state()
        self.assertTrue(Section.objects.get(id=section.id).has_reviews)

    def test_has_multiple(self):
        _, section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        instructor, _ = Instructor.objects.get_or_create(name="Rajiv Gandhi")
        section.instructors.add(instructor)
        import_review(
            section,
            instructor,
            None,
            10,
            None,
            {"instructor_quality": 4},
            lambda x, y: None,
        )
        import_review(
            section,
            instructor,
            None,
            10,
            None,
            {"course_quality": 4},
            lambda x, y=None: None,
        )
        fill_course_soft_state()
        self.assertTrue(Section.objects.get(id=section.id).has_reviews)


class OneReviewTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        self.instructor_pk = Instructor.objects.get(name=self.instructor_name).pk
        create_review(
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        Review.objects.all().update(enrollment=100)
        self.instructor_nores_pk = Instructor.objects.get(name="No Responses Instructor").pk

    def test_course(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(4, 4),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(4, 4)},
                    self.instructor_nores_pk: {},
                },
            },
        )
        self.assertEqual(len(res["instructors"]), 2)

    def test_instructor(self):
        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor_pk,
            {
                **average_and_recent(4, 4),
                "courses": {"CIS-120": {**average_and_recent(4, 4)}},
            },
        )

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {"courses": {"CIS-120": average_and_recent(4, 4)}},
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-120", self.instructor_pk],
            {"sections": [rating(4)]},
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-120", self.instructor_nores_pk],
            {
                "sections": [
                    {
                        "course_code": "CIS-120",
                        "semester": "2007C",
                        "forms_returned": 0,
                        "forms_produced": 100,
                    },
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
                        "desc": "CIS",
                        "url": f"/instructor/{self.instructor_pk}",
                    },
                ],
                "courses": [
                    {
                        "title": "CIS-120",
                        "desc": [""],
                        "url": f"/course/CIS-120/{TEST_SEMESTER}",
                    }
                ],
                "departments": [{"title": "CIS", "desc": "", "url": "/department/CIS"}],
            },
        )


class TwoSemestersOneInstructorTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        AddDropPeriod(semester="2012A").save()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
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
            {
                **average_and_recent(3, 4),
                "courses": {"CIS-120": average_and_recent(3, 4)},
            },
        )

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {"courses": {"CIS-120": average_and_recent(3, 4)}},
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["CIS-120", Instructor.objects.get(name=self.instructor_name).pk],
            {"sections": [rating(4), rating(2)]},
        )


class TwoSectionsOneSemesterTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review(
            "CIS-120-002",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 2},
        )

    def test_course(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 1,
                **average_and_recent(3, 3),
                "instructors": {
                    Instructor.objects.get(name=self.instructor_name).pk: {
                        **average_and_recent(3, 3),
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
                **average_and_recent(3, 3),
                "num_semesters": 1,
                "courses": {"CIS-120": average_and_recent(3, 3)},
            },
        )

    def test_department(self):
        self.assertRequestContainsAppx(
            "department-reviews",
            "CIS",
            {"courses": {"CIS-120": average_and_recent(3, 3)}},
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
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
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
            {
                "courses": {
                    "CIS-120": average_and_recent(3, 4),
                    "CIS-160": average_and_recent(2, 2),
                }
            },
        )


class TwoInstructorsOneSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
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
            {
                **average_and_recent(4, 4),
                "courses": {"CIS-120": average_and_recent(4, 4)},
            },
        )

        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2.pk,
            {
                **average_and_recent(2, 2),
                "courses": {"CIS-120": average_and_recent(2, 2)},
            },
        )


class TwoSectionTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-120-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})
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
            {
                **average_and_recent(4, 4),
                "courses": {"CIS-120": average_and_recent(4, 4)},
            },
        )

        self.assertRequestContainsAppx(
            "instructor-reviews",
            self.instructor2.pk,
            {
                **average_and_recent(2, 2),
                "courses": {"CIS-120": average_and_recent(2, 2)},
            },
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
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        create_review("CIS-120-001", "2017A", "Instructor Two", {"instructor_quality": 2})
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
                    self.instructor2.pk: {
                        **average_and_recent(1.5, 2),
                        "latest_semester": "2017A",
                    },
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
            "CIS-120-001",
            "2007C",
            "No Responses Instructor",
            {"instructor_quality": 0},
            responses=0,
        )
        _, recitation, _, _ = get_or_create_course_and_section("CIS-120-201", TEST_SEMESTER)
        recitation.activity = "REC"
        recitation.instructors.add(Instructor.objects.create(name="Instructor Two"))
        recitation.save()
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        self.instructor1 = Instructor.objects.get(name="Instructor One")
        self.instructor2 = Instructor.objects.get(name="Instructor Two")
        self.instructor_nores = Instructor.objects.get(name="No Responses Instructor")

    def test_course(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(4, 4),
                "instructors": {
                    self.instructor1.pk: average_and_recent(4, 4),
                    self.instructor_nores.pk: {},
                },
            },
        )
        self.assertEqual(2, len(res["instructors"]))


class RegistrationMetricsFlagTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        create_review("CIS-120-001", "2020A", "Instructor One", {"instructor_quality": 4})
        pdp_restriction = PreNGSSRestriction(
            code="PDP", description="Permission required from dept."
        )
        pdp_restriction.save()
        cis_120_001 = Section.objects.get(full_code="CIS-120-001")
        cis_120_001.pre_ngss_restrictions.add(pdp_restriction)
        cis_120_001.capacity = 100
        cis_120_001.save()
        StatusUpdate(
            section=Section.objects.get(full_code="CIS-120-001"),
            old_status="",
            new_status="O",
            alert_sent=False,
            request_body="",
        ).save()

        create_review("CIS-105-001", "2020A", "Instructor One", {"instructor_quality": 4})
        cis_105_001 = Section.objects.get(full_code="CIS-105-001")
        cis_105_001.capacity = 20
        cis_105_001.save()
        StatusUpdate(
            section=Section.objects.get(full_code="CIS-105-001"),
            old_status="",
            new_status="O",
            alert_sent=False,
            request_body="",
        ).save()

        create_review("OIDD-101-001", "2020A", "Instructor One", {"instructor_quality": 4})

        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_registration_metrics_pdp(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {"registration_metrics": False},
        )

    def test_registration_metrics_true(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-105",
            {"registration_metrics": True},
        )

    def test_registration_metrics_no_status_updates(self):
        self.assertRequestContainsAppx(
            "course-reviews",
            "OIDD-101",
            {"registration_metrics": False},
        )


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
            404,
            self.client.get(reverse("department-reviews", args=["BLAH"])).status_code,
        )

    def test_history(self):
        self.assertEqual(
            404,
            self.client.get(reverse("course-history", args=["BLAH", 123])).status_code,
        )

    def test_no_reviews(self):
        get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        self.assertEqual(
            404,
            self.client.get(reverse("course-reviews", args=["CIS-120"])).status_code,
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
            403,
            self.client.get(reverse("department-reviews", args=["BLAH"])).status_code,
        )

    def test_history(self):
        self.assertEqual(
            403,
            self.client.get(reverse("course-history", args=["BLAH", 0])).status_code,
        )


class RecitationInstructorTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review(
            "CIS-120-001",
            TEST_SEMESTER,
            self.instructor_name,
            {"instructor_quality": 4},
        )
        self.instructor_pk = Instructor.objects.get(name=self.instructor_name).pk

        rec_instructor = Instructor(name="Recitation Instructor")
        rec_instructor.save()
        self.rec_instructor_pk = rec_instructor.pk
        _, rec_section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        rec_section.activity = "REC"
        rec_section.save()
        rec_section.instructors.add(rec_instructor)

        create_review(
            "CIS-120-002",
            "2007C",
            self.instructor_name,
            {"instructor_quality": 0},
            responses=0,
        )
        Review.objects.all().update(enrollment=100)

    def test_course(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                **average_and_recent(4, 4),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(4, 4)},
                },
            },
        )
        self.assertEqual(len(res["instructors"]), 1)

    def test_autocomplete(self):
        res = self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "CIS",
                        "url": f"/instructor/{self.instructor_pk}",
                    },
                ],
                "courses": [
                    {
                        "title": "CIS-120",
                        "desc": [""],
                        "url": f"/course/CIS-120/{TEST_SEMESTER}",
                    }
                ],
                "departments": [{"title": "CIS", "desc": "", "url": "/department/CIS"}],
            },
        )
        self.assertEqual(len(res["instructors"]), 1)


class DuplicateCodeTestCase(TestCase, PCRTestMixin):
    def setUp(self):
        set_semester()
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))
        create_review("CIS-120-001", "2019C", self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 3})
        create_review("CIS-120-001", "2011B", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-120-001", "2010C", self.instructor_name, {"instructor_quality": 1})
        # Topics:
        # - CIS-120 2019C
        # - CIS-120 2012A, CIS-120 2011B
        # - CIS-120 2010C
        new_course = Course.objects.get(full_code="CIS-120", semester="2019C")
        new_course.parent_course = None
        new_course.manually_set_parent_course = True
        new_course.save()
        old_course_b = Course.objects.get(full_code="CIS-120", semester="2011B")
        old_course_b.parent_course = None
        old_course_b.manually_set_parent_course = True
        old_course_b.save()
        old_course_c = Course.objects.get(full_code="CIS-120", semester="2010C")
        old_course_c.parent_course = None
        old_course_c.manually_set_parent_course = True
        old_course_c.save()
        fill_course_soft_state()

        self.instructor_pk = Instructor.objects.get(name=self.instructor_name).pk

    def test_course(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 1,
                **average_and_recent(4, 4),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(4, 4)},
                },
            },
        )
        self.assertEqual(len(res["instructors"]), 1)

    def test_course_semester(self):
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 1,
                **average_and_recent(4, 4),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(4, 4)},
                },
            },
            query_params={"semester": "2019C"},
        )
        self.assertEqual(len(res["instructors"]), 1)
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 2,
                **average_and_recent(2.5, 3),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(2.5, 3)},
                },
            },
            query_params={"semester": "2012A"},
        )
        self.assertEqual(len(res["instructors"]), 1)
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 2,
                **average_and_recent(2.5, 3),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(2.5, 3)},
                },
            },
            query_params={"semester": "2011B"},
        )
        self.assertEqual(len(res["instructors"]), 1)
        res = self.assertRequestContainsAppx(
            "course-reviews",
            "CIS-120",
            {
                "num_semesters": 1,
                **average_and_recent(1, 1),
                "instructors": {
                    self.instructor_pk: {**average_and_recent(1, 1)},
                },
            },
            query_params={"semester": "2010C"},
        )
        self.assertEqual(len(res["instructors"]), 1)

    def test_autocomplete(self):
        res = self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "CIS",
                        "url": f"/instructor/{self.instructor_pk}",
                    },
                ],
                "courses": [
                    {
                        "title": "(Fall 2010) CIS-120",
                        "desc": [""],
                        "url": "/course/CIS-120/2010C",
                    },
                    {
                        "title": "(Fall 2019) CIS-120",
                        "desc": [""],
                        "url": "/course/CIS-120/2019C",
                    },
                    {
                        "title": "(Spring 2012) CIS-120",
                        "desc": [""],
                        "url": "/course/CIS-120/2012A",
                    },
                ],
                "departments": [{"title": "CIS", "desc": "", "url": "/department/CIS"}],
            },
        )
        self.assertEqual(len(res["instructors"]), 1)
