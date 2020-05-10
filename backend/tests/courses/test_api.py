from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient
from tests.courses.util import create_mock_data

from courses.models import Department, Instructor, Requirement
from courses.util import get_or_create_course


TEST_SEMESTER = "2019A"


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()


class CourseListTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_get_courses(self):
        response = self.client.get("/api/courses/all/courses/")
        self.assertEqual(len(response.data), 2)
        course_codes = [d["id"] for d in response.data]
        self.assertTrue("CIS-120" in course_codes and "MATH-114" in course_codes)
        self.assertTrue(1, response.data[0]["num_sections"])
        self.assertTrue(1, response.data[1]["num_sections"])

    def test_semester_setting(self):
        new_sem = TEST_SEMESTER[:-1] + "Z"
        create_mock_data("MATH-104-001", new_sem)

        response = self.client.get(f"/api/courses/{TEST_SEMESTER}/courses/")
        self.assertEqual(len(response.data), 2)

        response = self.client.get(f"/api/courses/{new_sem}/courses/")
        self.assertEqual(len(response.data), 1)

        response = self.client.get("/api/courses/all/courses/")
        self.assertEqual(len(response.data), 3)

    def test_current_semester(self):
        new_sem = TEST_SEMESTER[:-1] + "Z"
        create_mock_data("MATH-104-001", new_sem)
        response = self.client.get(f"/api/courses/current/courses/")
        self.assertEqual(len(response.data), 2)

    def test_course_with_no_sections_not_in_list(self):
        self.math.sections.all().delete()
        response = self.client.get("/api/courses/all/courses/")
        self.assertEqual(len(response.data), 1, response.data)

    def test_course_with_cancelled_sections_not_in_list(self):
        self.math1.status = "X"
        self.math1.save()
        response = self.client.get("/api/courses/all/courses/")
        self.assertEqual(response.data[1]["num_sections"], 0, response.data)


class CourseDetailTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        i = Instructor(name="Test Instructor")
        i.save()
        self.section.instructors.add(i)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_get_course(self):
        course, section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        response = self.client.get("/api/courses/all/courses/CIS-120/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEqual("Test Instructor", response.data["sections"][0]["instructors"][0])

    def test_section_cancelled(self):
        course, section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        section.credits = 1
        section.status = "X"
        section.save()
        response = self.client.get("/api/courses/all/courses/CIS-120/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_section_no_credits(self):
        course, section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        section.credits = None
        section.save()
        response = self.client.get("/api/courses/all/courses/CIS-120/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_course_no_good_sections(self):
        self.section.status = "X"
        self.section.save()
        response = self.client.get("/api/courses/all/courses/CIS-120/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 0)

    def test_not_get_course(self):
        response = self.client.get("/api/courses/all/courses/CIS-160/")
        self.assertEqual(response.status_code, 404)


class SectionSearchTestCase(TestCase):
    def setUp(self):
        create_mock_data("CIS-120-001", TEST_SEMESTER)
        create_mock_data("CIS-160-001", TEST_SEMESTER)
        create_mock_data("CIS-120-201", TEST_SEMESTER)
        create_mock_data("PSCI-181-001", TEST_SEMESTER)
        self.client = APIClient()

    def test_match_exact(self):
        res = self.client.get(reverse("section-search"), {"search": "CIS-120-001"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_exact_spaces(self):
        res = self.client.get(reverse("section-search"), {"search": "CIS 120 001"})
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_exact_nosep(self):
        res = self.client.get(reverse("section-search"), {"search": "PSCI181001"})
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("PSCI-181-001", res.data[0]["section_id"])

    def test_match_full_course_nosep(self):
        res = self.client.get(reverse("section-search"), {"search": "CIS120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_full_course_exact(self):
        res = self.client.get(reverse("section-search"), {"search": "CIS-120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_full_course_space(self):
        res = self.client.get(reverse("section-search"), {"search": "PSCI 181"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))

    def test_match_department(self):
        res = self.client.get(reverse("section-search"), {"search": "CIS"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(3, len(res.data))

    def test_match_lowercase(self):
        res = self.client.get(reverse("section-search"), {"search": "cis120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))

    def test_nomatch(self):
        res = self.client.get(reverse("section-search"), {"search": "123bdfsh3wq!@#"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(0, len(res.data))


class RequirementListTestCase(TestCase):
    def setUp(self):
        set_semester()
        get_or_create_course(
            "CIS", "120", "2012A"
        )  # dummy course to make sure we're filtering by semester
        self.course, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        self.course2, _ = get_or_create_course("CIS", "125", TEST_SEMESTER)
        self.department = Department.objects.get(code="CIS")

        self.req1 = Requirement(semester=TEST_SEMESTER, school="SAS", code="TEST1", name="Test 1")
        self.req2 = Requirement(semester=TEST_SEMESTER, school="SAS", code="TEST2", name="Test 2")
        self.req3 = Requirement(semester="XXXXX", school="SAS", code="TEST1", name="Test 1+")

        self.req1.save()
        self.req2.save()
        self.req3.save()

        self.req1.departments.add(self.department)
        self.req1.overrides.add(self.course2)
        self.req2.courses.add(self.course)
        self.req2.courses.add(self.course2)
        self.req3.departments.add(self.department)

        self.client = APIClient()

    def test_requirement_route(self):
        response = self.client.get(reverse("requirements-list", kwargs={"semester": "current"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(response.data))

    def test_requirement_route_other_sem(self):
        response = self.client.get(reverse("requirements-list", kwargs={"semester": "XXXXX"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.data))
