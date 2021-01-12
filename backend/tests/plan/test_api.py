from django.test import RequestFactory, TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient
from tests.courses.util import (
    create_mock_async_class,
    create_mock_data,
    create_mock_data_days,
    create_mock_data_multiple_meetings,
)

from courses.models import Instructor, Requirement
from plan.search import TypedCourseSearchBackend
from review.models import Review


TEST_SEMESTER = "2019C"


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()


class TypedSearchBackendTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.search = TypedCourseSearchBackend()

    def test_type_course(self):
        req = self.factory.get("/", {"type": "course", "search": "ABC123"})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(["^full_code"], terms)

    def test_type_keyword(self):
        req = self.factory.get("/", {"type": "keyword", "search": "ABC123"})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(["title", "sections__instructors__name"], terms)

    def test_auto_course(self):
        courses = ["cis", "CIS", "cis120", "anch-027", "cis 121", "ling-140"]
        for course in courses:
            req = self.factory.get("/", {"type": "auto", "search": course})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(["^full_code"], terms, f"search:{course}")

    def test_auto_keyword(self):
        keywords = ["rajiv", "gandhi", "programming", "hello world"]
        for kw in keywords:
            req = self.factory.get("/", {"type": "auto", "search": kw})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(["title", "sections__instructors__name"], terms, f"search:{kw}")


class CourseSearchTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_search_by_dept(self):
        response = self.client.get(
            reverse("courses-current-list"), {"search": "math", "type": "auto"}
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.data), 1)
        course_codes = [d["id"] for d in response.data]
        self.assertTrue("CIS-120" not in course_codes and "MATH-114" in course_codes)

    def test_search_by_instructor(self):
        self.section.instructors.add(Instructor.objects.get_or_create(name="Tiffany Chang")[0])
        self.math1.instructors.add(Instructor.objects.get_or_create(name="Josh Doman")[0])
        searches = ["Tiffany", "Chang"]
        for search in searches:
            response = self.client.get(
                reverse("courses-current-list"), {"search": search, "type": "auto"}
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(len(response.data), 1)
            course_codes = [d["id"] for d in response.data]
            self.assertTrue(
                "CIS-120" in course_codes and "MATH-114" not in course_codes, f"search:{search}"
            )


class CreditUnitFilterTestCase(TestCase):
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
        response = self.client.get(reverse("courses-current-list"), {"cu": "1.0"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_include_multiple(self):
        response = self.client.get(reverse("courses-current-list"), {"cu": "0.5,1.0"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_exclude_course(self):
        response = self.client.get(reverse("courses-current-list"), {"cu": ".5,1.5"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


class RequirementFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.different_math, self.different_math1 = create_mock_data(
            "MATH-116-001", ("2019A" if TEST_SEMESTER == "2019C" else "2019C")
        )
        self.req = Requirement(semester=TEST_SEMESTER, code="REQ", school="SAS")
        self.req.save()
        self.req.courses.add(self.math)
        self.client = APIClient()
        set_semester()

    def test_return_all_courses(self):
        response = self.client.get(reverse("courses-current-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_filter_for_req(self):
        response = self.client.get(reverse("courses-current-list"), {"requirements": "REQ@SAS"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])

    def test_filter_for_req_dif_sem(self):
        req2 = Requirement(
            semester=("2019A" if TEST_SEMESTER == "2019C" else "2019C"), code="REQ", school="SAS"
        )
        req2.save()
        req2.courses.add(self.different_math)
        response = self.client.get(reverse("courses-current-list"), {"requirements": "REQ@SAS"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])
        self.assertEqual(TEST_SEMESTER, response.data[0]["semester"])

    def test_multi_req(self):
        course3, section3 = create_mock_data("CIS-240-001", TEST_SEMESTER)
        req2 = Requirement(semester=TEST_SEMESTER, code="REQ2", school="SEAS")
        req2.save()
        req2.courses.add(course3)

        response = self.client.get(
            reverse("courses-current-list"), {"requirements": "REQ@SAS,REQ2@SEAS"}
        )
        self.assertEqual(0, len(response.data))

    def test_double_count_req(self):
        req2 = Requirement(semester=TEST_SEMESTER, code="REQ2", school="SEAS")
        req2.save()
        req2.courses.add(self.math)
        response = self.client.get(
            reverse("courses-current-list"), {"requirements": "REQ@SAS,REQ2@SEAS"}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual("MATH-114", response.data[0]["id"])


class CourseReviewAverageTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        _, self.section2 = create_mock_data("CIS-120-002", TEST_SEMESTER)
        self.instructor = Instructor(name="Person1")
        self.instructor.save()
        self.rev1 = Review(
            section=create_mock_data("CIS-120-003", "2005C")[1], instructor=self.instructor
        )
        self.rev1.save()
        self.rev1.set_averages(
            {"course_quality": 4, "instructor_quality": 4, "difficulty": 4,}
        )
        self.instructor2 = Instructor(name="Person2")
        self.instructor2.save()
        self.rev2 = Review(
            section=create_mock_data("CIS-120-002", "2015A")[1], instructor=self.instructor2
        )
        self.rev2.instructor = self.instructor2
        self.rev2.save()
        self.rev2.set_averages(
            {"course_quality": 2, "instructor_quality": 2, "difficulty": 2,}
        )

        self.section.instructors.add(self.instructor)
        self.section2.instructors.add(self.instructor2)
        self.client = APIClient()
        set_semester()

    def test_course_average(self):
        response = self.client.get(reverse("courses-current-detail", args=["CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.data["course_quality"])
        self.assertEqual(3, response.data["instructor_quality"])
        self.assertEqual(3, response.data["difficulty"])

    def test_section_reviews(self):
        response = self.client.get(reverse("courses-current-detail", args=["CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["sections"]))

    def test_section_no_duplicates(self):
        instructor3 = Instructor(name="person3")
        instructor3.save()
        rev3 = Review(section=self.rev2.section, instructor=instructor3)
        rev3.save()
        rev3.set_averages(
            {"course_quality": 1, "instructor_quality": 1, "difficulty": 1,}
        )
        self.section2.instructors.add(instructor3)
        response = self.client.get(reverse("courses-current-detail", args=["CIS-120"]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data["sections"]))
        self.assertEqual(
            1.5, response.data["sections"][1]["course_quality"], response.data["sections"][1]
        )

    def test_filter_courses_by_review_included(self):
        response = self.client.get(reverse("courses-current-list"), {"difficulty": "2.5-3.5"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_filter_courses_by_review_excluded(self):
        response = self.client.get(reverse("courses-current-list"), {"difficulty": "0-2"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


class DayFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section1 = create_mock_data_days("CIS-120-001", TEST_SEMESTER)
        _, self.section2 = create_mock_data_days(
            code="CIS-120-002", semester=TEST_SEMESTER, days="TR"
        )
        _, self.section3 = create_mock_data_days(
            code="CIS-160-001", semester=TEST_SEMESTER, days="F"
        )
        _, self.section4 = create_mock_data_days(
            code="CIS-160-002", semester=TEST_SEMESTER, days="S"
        )
        _, self.section7 = create_mock_data_multiple_meetings(
            code="CIS-121-002", semester=TEST_SEMESTER
        )

        # asynchronous so should always show up
        _, self.section8 = create_mock_async_class(code="CIS-262-001", semester=TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_no_days_passed_in(self):
        response = self.client.get(reverse("courses-current-list"), {})
        self.assertEqual(4, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-160", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_all_days(self):
        response = self.client.get(reverse("courses-current-list"), {"days": "MTWRFS"})
        self.assertEqual(4, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-160", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_no_days(self):
        # only async
        response = self.client.get(reverse("courses-current-list"), {"days": ""})
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["id"], "CIS-262")
        self.assertEqual(200, response.status_code)

    def test_both_sections_work(self):
        response = self.client.get(reverse("courses-current-list"), {"days": "FS"})
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-160", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_one_section_works(self):
        response = self.client.get(reverse("courses-current-list"), {"days": "FS"})
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-160", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_all_meetings_work(self):
        response = self.client.get(reverse("courses-current-list"), {"days": "MTWR"})
        self.assertEqual(3, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_one_meeting_works(self):
        response = self.client.get(reverse("courses-current-list"), {"days": "MT"})
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)


class TimeFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section1 = create_mock_data_days("CIS-120-001", TEST_SEMESTER)
        _, self.section2 = create_mock_data_days(
            code="CIS-120-002", semester=TEST_SEMESTER, start=12.0, end=13.0
        )
        _, self.section3 = create_mock_data_days(
            code="CIS-160-001", semester=TEST_SEMESTER, start=1.0, end=5.0
        )
        _, self.section4 = create_mock_data_days(
            code="CIS-160-002", semester=TEST_SEMESTER, start=2.0, end=4.0
        )
        _, self.section7 = create_mock_data_multiple_meetings(
            code="CIS-121-002", semester=TEST_SEMESTER
        )

        # asynchronous so should always show up
        _, self.section8 = create_mock_async_class(code="CIS-262-001", semester=TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_null_passed(self):
        response = self.client.get(reverse("courses-current-list"), {})
        self.assertEqual(4, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-160", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_all_times(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 0.0, "end_time": 23.59}
        )
        self.assertEqual(4, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-160", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_outside_bounds(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": -15.0, "end_time": 42.0}
        )
        self.assertEqual(4, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-120", "CIS-160", "CIS-121", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_crossover_times(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 15.0, "end_time": 2.0}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_no_days_start_end_same(self):
        # only async
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 5.5, "end_time": 5.5}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]["id"], "CIS-262")
        self.assertEqual(200, response.status_code)

    def test_only_one_section_works(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 1.0, "end_time": 4.2}
        )
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-160", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_both_sections_works(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 1.0, "end_time": 5.5}
        )
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-160", "CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_contains_parts_not_whole_sec(self):
        response = self.client.get(
            # only contains part of first sec for CIS 120 and second sec for CIS 120
            # starts and ends at different places
            reverse("courses-current-list"),
            {"start_time": 11.5, "end_time": 12.5},
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_contains_whole_sec(self):
        response = self.client.get(
            # only contains part of first sec for CIS 120 and second sec for CIS 120
            # starts and ends at different places
            reverse("courses-current-list"),
            {"start_time": 11.0, "end_time": 12.0},
        )
        self.assertEqual(2, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262", "CIS-120"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_only_one_meeting_works(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 21.0, "end_time": 22.0}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)

    def test_both_meetings_work(self):
        response = self.client.get(
            reverse("courses-current-list"), {"start_time": 20.0, "end_time": 22.0}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual(200, response.status_code)
        all_codes = ["CIS-262"]
        for res in response.data:
            self.assertIn(res["id"], all_codes)
