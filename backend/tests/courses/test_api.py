import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient
from tests.courses.util import create_mock_data

from courses.models import Department, Instructor, Requirement
from courses.search import TypedCourseSearchBackend
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
        response = self.client.get(reverse("courses-list", kwargs={"semester": "all"}))
        self.assertEqual(len(response.data), 2)
        course_codes = [d["id"] for d in response.data]
        self.assertTrue("CIS-120" in course_codes and "MATH-114" in course_codes)
        self.assertTrue(1, response.data[0]["num_sections"])
        self.assertTrue(1, response.data[1]["num_sections"])

    def test_semester_setting(self):
        new_sem = TEST_SEMESTER[:-1] + "Z"
        create_mock_data("MATH-104-001", new_sem)

        response = self.client.get(reverse("courses-list", kwargs={"semester": TEST_SEMESTER}))
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse("courses-list", kwargs={"semester": new_sem}))
        self.assertEqual(len(response.data), 1)

        response = self.client.get(reverse("courses-list", kwargs={"semester": "all"}))
        self.assertEqual(len(response.data), 3)

    def test_current_semester(self):
        new_sem = TEST_SEMESTER[:-1] + "Z"
        response = self.client.get(reverse("courses-list", kwargs={"semester": "current"}))
        create_mock_data("MATH-104-001", new_sem)
        self.assertEqual(len(response.data), 2)

    def test_course_with_no_sections_not_in_list(self):
        self.math.sections.all().delete()
        response = self.client.get(reverse("courses-list", kwargs={"semester": "all"}))
        self.assertEqual(len(response.data), 1, response.data)

    def test_course_with_cancelled_sections_not_in_list(self):
        self.math1.status = "X"
        self.math1.save()
        response = self.client.get(reverse("courses-list", kwargs={"semester": "all"}))
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
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-120"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEqual("Test Instructor", response.data["sections"][0]["instructors"][0]["name"])

    def test_section_cancelled(self):
        course, section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        section.credits = 1
        section.status = "X"
        section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-120"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_section_no_credits(self):
        course, section = create_mock_data("CIS-120-201", TEST_SEMESTER)
        section.credits = None
        section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-120"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_course_no_good_sections(self):
        self.section.status = "X"
        self.section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-120"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-120")
        self.assertEqual(len(response.data["sections"]), 0)

    def test_not_get_course(self):
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-160"})
        )
        self.assertEqual(response.status_code, 404)


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
            reverse("courses-search", args=["current"]), {"search": "math", "type": "auto"}
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
                reverse("courses-search", args=["current"]), {"search": search, "type": "auto"}
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(len(response.data), 1)
            course_codes = [d["id"] for d in response.data]
            self.assertTrue(
                "CIS-120" in course_codes and "MATH-114" not in course_codes, f"search:{search}"
            )


class SectionSearchTestCase(TestCase):
    def setUp(self):
        create_mock_data("CIS-120-001", TEST_SEMESTER)
        create_mock_data("CIS-160-001", TEST_SEMESTER)
        create_mock_data("CIS-120-201", TEST_SEMESTER)
        create_mock_data("PSCI-181-001", TEST_SEMESTER)
        self.client = APIClient()

    def test_match_exact(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "CIS-120-001"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_exact_spaces(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "CIS 120 001"}
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_exact_nosep(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "PSCI181001"})
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("PSCI-181-001", res.data[0]["section_id"])

    def test_match_full_course_nosep(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_full_course_exact(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS-120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-120-001", res.data[0]["section_id"])

    def test_match_full_course_space(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "PSCI 181"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))

    def test_match_department(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(3, len(res.data))

    def test_match_lowercase(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "cis120"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))

    def test_nomatch(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "123bdfsh3wq!@#"}
        )
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


class SectionListTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_sections_appear(self):
        response = self.client.get(
            reverse("section-search", args=["current"]), kwargs={"semester": TEST_SEMESTER}
        )
        course_codes = [d["section_id"] for d in response.data]
        self.assertTrue("CIS-120-001" in course_codes and "MATH-114-001" in course_codes)
        self.assertEqual(2, len(response.data))

    def test_section_without_(self):
        self.math1.activity = ""
        self.math1.save()
        response = self.client.get(
            reverse("section-search", args=["current"]), kwargs={"semester": TEST_SEMESTER}
        )
        self.assertEqual(1, len(response.data))
        self.assertEqual("CIS-120-001", response.data[0]["section_id"])


class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="jacob", password="top_secret")
        self.client = APIClient()
        self.client.login(username="jacob", password="top_secret")

    def test_patch(self):
        response = self.client.patch(
            "/accounts/me/",
            json.dumps({"first_name": "new_name"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["first_name"], "new_name")
        response = self.client.patch(
            "/accounts/me/",
            json.dumps({"profile": {"phone": "3131234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["first_name"], "new_name")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")

    def test_settings_before_create(self):
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertFalse(response.data["profile"]["push_notifications"])

    def test_update_settings(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": True,
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_update_settings_change_first_name(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "newname",
                    "last_name": "",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "newname")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "newname")
        self.assertEqual(response.data["last_name"], "")

    def test_update_settings_change_last_name(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "",
                    "last_name": "newname",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "newname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "newname")

    def test_update_settings_change_username(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "username": "newusername",
                    "first_name": "",
                    "last_name": "",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_add_fields(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "",
                    "last_name": "",
                    "middle_name": "m",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": True,
                        "favorite_color": "blue",
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertFalse("favorite_color" in response.data["profile"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertFalse("middle_name" in response.data)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertFalse("favorite_color" in response.data["profile"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertFalse("middle_name" in response.data)

    def test_ignore_fields_email_update(self):
        self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "fname",
                    "last_name": "lname",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-view"),
            json.dumps({"profile": {"email": "example2@email.com"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")

    def test_ignore_fields_phone_update(self):
        self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "fname",
                    "last_name": "lname",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": True,
                    },
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-view"),
            json.dumps({"profile": {"phone": "2121234567"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")

    def test_ignore_fields_push_notifications_update(self):
        """
        Tests that you can update just the push notification setting without specifying any other
        settings, and those other settings will not be changed.
        """
        self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "first_name": "fname",
                    "last_name": "lname",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-view"),
            json.dumps({"profile": {"push_notifications": True}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")

    def test_invalid_phone(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example@email.com",
                        "phone": "abc",
                        "push_notifications": True,
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])

    def test_invalid_email(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example@",
                        "phone": "3131234567",
                        "push_notifications": True,
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])

    def test_null_email(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {"profile": {"email": None, "phone": "3131234567", "push_notifications": True}}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_null_phone(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example@email.com",
                        "phone": None,
                        "push_notifications": True,
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_both_null(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps({"profile": {"email": None, "phone": None, "push_notifications": True}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], None)
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_push_notifications_non_boolean(self):
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "username": "newusername",
                    "first_name": "",
                    "last_name": "",
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": "Rand",
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(None, response.data["profile"]["email"])
        self.assertEqual(None, response.data["profile"]["phone"])
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual("jacob", response.data["username"])
        self.assertEqual("", response.data["first_name"])
        self.assertEqual("", response.data["last_name"])

    def test_multiple_users_independent(self):
        User.objects.create_user(username="murey", password="top_secret")
        client2 = APIClient()
        client2.login(username="murey", password="top_secret")
        response = self.client.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example@email.com",
                        "phone": "3131234567",
                        "push_notifications": "True",
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+13131234567")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = client2.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example2@email.com",
                        "phone": "2121234567",
                        "push_notifications": "False",
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "murey")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = client2.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12121234567")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "murey")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")

    def test_user_not_logged_in(self):
        client2 = APIClient()
        response = client2.put(
            reverse("user-view"),
            json.dumps(
                {
                    "profile": {
                        "email": "example2@email.com",
                        "phone": "2121234567",
                        "push_notifications": "True",
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(403, response.status_code)
        response = client2.get(reverse("user-view"))
        self.assertEqual(403, response.status_code)


class DocumentationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_no_error(self):
        response = self.client.get(reverse("openapi-schema"))
        self.assertEqual(response.status_code, 200)

    def test_no_error_multiple_times(self):
        response = self.client.get(reverse("openapi-schema"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("openapi-schema"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("openapi-schema"))
        self.assertEqual(response.status_code, 200)
