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


class OneReviewTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        i1 = res.data.get("instructors").get(self.instructor_name)
        i1_averages = i1.get("average_reviews")
        i1_recents = i1.get("recent_reviews")
        self.assertEqual(1, res.data.get("num_semesters"))
        for d in [averages, recent, i1_averages, i1_recents]:
            for dp in [averages, recent, i1_averages, i1_recents]:
                self.assertDictEqual(d, dp)

    def test_instructor(self):
        res = self.client.get(reverse("instructor-reviews", args=[Instructor.objects.get().pk]))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        c1 = res.data.get("courses").get("CIS-120")
        c1_averages = c1.get("average_reviews")
        c1_recents = c1.get("recent_reviews")
        self.assertEqual(1, len(res.data.get("courses")))
        for d in [averages, recent, c1_averages, c1_recents]:
            for dp in [averages, recent, c1_averages, c1_recents]:
                self.assertDictEqual(d, dp)

    def test_department(self):
        res = self.client.get(reverse("department-reviews", args=["CIS"]))
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data.get("courses")))
        self.assertEqual(
            4, res.data.get("courses")[0].get("average_reviews").get("rInstructorQuality")
        )
        self.assertEqual(
            4, res.data.get("courses")[0].get("recent_reviews").get("rInstructorQuality")
        )

    def test_history(self):
        res = self.client.get(
            reverse("course-history", args=["CIS-120", Instructor.objects.get().pk])
        )
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data.get("sections")))
        self.assertEqual(4, res.data.get("sections")[0].get("ratings").get("rInstructorQuality"))

    def test_autocomplete(self):
        set_semester()
        res = self.client.get(reverse("review-autocomplete"))
        self.assertEqual(200, res.status_code)
        self.assertDictEqual(
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "CIS",
                        "url": reverse("instructor-reviews", args=[Instructor.objects.get().pk]),
                    }
                ],
                "courses": [
                    {
                        "title": "CIS-120",
                        "desc": [""],
                        "url": reverse("course-reviews", args=["CIS-120"]),
                    }
                ],
                "departments": [
                    {"title": "CIS", "desc": "", "url": reverse("department-reviews", args=["CIS"])}
                ],
            },
            res.data,
        )


class TwoSemestersOneInstructorTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        i1 = res.data.get("instructors").get(self.instructor_name)
        i1_averages = i1.get("average_reviews")
        i1_recents = i1.get("recent_reviews")
        self.assertEqual(2, res.data.get("num_semesters"))
        self.assertEqual(3, averages.get("rInstructorQuality"))
        self.assertEqual(4, recent.get("rInstructorQuality"))
        self.assertEqual(3, i1_averages.get("rInstructorQuality"))
        self.assertEqual(4, i1_recents.get("rInstructorQuality"))
        self.assertEqual(TEST_SEMESTER, i1.get("latest_semester"))


class SemesterWithFutureCourseTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-160-001", "3008C", self.instructor_name, {"instructor_quality": 2})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        i1 = res.data.get("instructors").get(self.instructor_name)
        i1_averages = i1.get("average_reviews")
        i1_recents = i1.get("recent_reviews")
        self.assertEqual(2, res.data.get("num_semesters"))
        self.assertEqual(3, averages.get("rInstructorQuality"))
        self.assertEqual(4, recent.get("rInstructorQuality"))
        self.assertEqual(3, i1_averages.get("rInstructorQuality"))
        self.assertEqual(4, i1_recents.get("rInstructorQuality"))
        self.assertEqual(TEST_SEMESTER, i1.get("latest_semester"))


class TwoInstructorsOneSectionTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        self.assertEqual(3, averages.get("rInstructorQuality"))
        self.assertEqual(3, recent.get("rInstructorQuality"))
        self.assertEqual(
            4,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            4,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            2,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            2,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )


class TwoSectionTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-002", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        self.assertEqual(3, averages.get("rInstructorQuality"))
        self.assertEqual(3, recent.get("rInstructorQuality"))
        self.assertEqual(
            4,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            4,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            2,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            2,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )


def TwoInstructorsMultipleSemestersTestCase(TestCase):
    def setUp(self):
        self.instructor_name = "Instructor One"
        self.client = APIClient()
        create_review("CIS-120-001", TEST_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        create_review("CIS-120-900", "2012A", self.instructor_name, {"instructor_quality": 2})
        create_review("CIS-120-003", "2012C", "Instructor Two", {"instructor_quality": 1})
        create_review("CIS-120-001", TEST_SEMESTER, "Instructor Two", {"instructor_quality": 2})

    def test_course(self):
        res = self.client.get(reverse("course-reviews", kwargs={"course_code": "CIS-120"}))
        self.assertEqual(200, res.status_code)
        averages = res.data.get("average_reviews")
        recent = res.data.get("recent_reviews")
        self.assertEqual(2.25, averages.get("rInstructorQuality"))
        self.assertEqual(2.25, recent.get("rInstructorQuality"))
        self.assertEqual(
            3,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            3,
            res.data.get("instructors")
            .get(self.instructor_name)
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            1.5,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("average_reviews")
            .get("rInstructorQuality"),
        )
        self.assertEqual(
            1.5,
            res.data.get("instructors")
            .get("Instructor Two")
            .get("recent_reviews")
            .get("rInstructorQuality"),
        )
