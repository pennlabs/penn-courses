import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import RequestFactory, TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import (
    Attribute,
    Course,
    Department,
    Instructor,
    NGSSRestriction,
    PreNGSSRequirement,
    Comment
)
from courses.search import TypedCourseSearchBackend
from courses.util import (
    get_or_create_course,
    get_or_create_course_and_section,
    invalidate_current_semester_cache,
)
from plan.models import Schedule
from tests import production_CourseListSearch_get_serializer_context
from tests.courses.util import create_mock_data, fill_course_soft_state
from tests.plan.test_course_recs import CourseRecommendationsTestCase


TEST_SEMESTER = "2019A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class CourseListTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()

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
        set_semester()
        self.course, self.section = create_mock_data("CIS-1200-001", TEST_SEMESTER)
        old_course, _ = create_mock_data("CIS-120-001", "2018C")
        self.course.parent_course = old_course
        self.course.manually_set_parent_course = True
        self.course.save()
        fill_course_soft_state()
        i = Instructor(name="Test Instructor")
        i.save()
        self.section.instructors.add(i)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()

    def test_get_course(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-1200")
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEqual("Test Instructor", response.data["sections"][0]["instructors"][0]["name"])

    def test_check_offered_in(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "CIS-120@2018C"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-1200")
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEqual("Test Instructor", response.data["sections"][0]["instructors"][0]["name"])

    def test_check_offered_in_fail_code(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "CIS-1200@2018C"},
        )
        self.assertEqual(404, response.status_code)

    def test_check_offered_in_fail_semester(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "CIS-120@2018A"},
        )
        self.assertEqual(404, response.status_code)

    def test_check_offered_in_malformed(self):
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "CIS-120@"},
        )
        self.assertEqual(404, response.status_code)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "@2018C"},
        )
        self.assertEqual(404, response.status_code)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "2018C"},
        )
        self.assertEqual(400, response.status_code)
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"}),
            {"check_offered_in": "CIS-120@2018C@"},
        )
        self.assertEqual(400, response.status_code)

    def test_section_cancelled(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        section.credits = 1
        section.status = "X"
        section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-1200")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_section_no_credits(self):
        course, section = create_mock_data("CIS-1200-201", TEST_SEMESTER)
        section.credits = None
        section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-1200")
        self.assertEqual(len(response.data["sections"]), 1, response.data["sections"])

    def test_course_no_good_sections(self):
        self.section.status = "X"
        self.section.save()
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-1200"})
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["id"], "CIS-1200")
        self.assertEqual(len(response.data["sections"]), 0)

    def test_not_get_course(self):
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": "CIS-160"})
        )
        self.assertEqual(response.status_code, 404)


class TypedSearchBackendTestCase(TestCase):
    def setUp(self):
        set_semester()
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

    def test_auto_keyword_both(self):
        keywords = ["rajiv", "gandhi"]
        for kw in keywords:
            req = self.factory.get("/", {"type": "auto", "search": kw})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(
                ["^full_code", "title", "sections__instructors__name"], terms, f"search:{kw}"
            )

    def test_auto_keyword_only(self):
        keywords = ["hello world", "discrete math", "programming"]
        for kw in keywords:
            req = self.factory.get("/", {"type": "auto", "search": kw})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(["title", "sections__instructors__name"], terms, f"search:{kw}")


class CourseSearchTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()

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


class CourseSearchRecommendationScoreTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up test data according to CourseRecommendationTestCase
        CourseRecommendationsTestCase.setUpTestData()
        cls.course_clusters = CourseRecommendationsTestCase.course_clusters

    def setUp(self):
        set_semester()
        self.username = "jacob"
        self.password = "top_secret"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client = APIClient()

    def test_recommendation_is_null_when_course_not_part_of_model_even_when_logged_in(self):
        self.client.login(username=self.username, password=self.password)

        self.course, self.section = create_mock_data("PSCI-437-001", TEST_SEMESTER)
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"search": "PSCI-437", "type": "auto"}
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.data), 1)
        self.assertIsNone(response.data[0]["recommendation_score"])

    def test_recommendation_is_null_when_user_not_logged_in(self):
        response = self.client.get(
            reverse("courses-search", args=["current"]), {"search": "PSCI", "type": "auto"}
        )

        self.assertEqual(200, response.status_code)
        for course in response.data:
            self.assertEqual(course["recommendation_score"], None)

    @patch(
        "courses.views.CourseListSearch.get_serializer_context",
        new=production_CourseListSearch_get_serializer_context,
    )
    @patch("courses.views.retrieve_course_clusters")
    def test_recommendation_is_number_when_user_is_logged_in(self, course_clusters_mock):
        course_clusters_mock.return_value = self.course_clusters
        self.client.login(username=self.username, password=self.password)

        curr_semester_schedule = Schedule.objects.create(
            person=self.user, name="curr_semester_schedule", semester=TEST_SEMESTER
        )
        curr_semester_schedule.save()
        # NOTE: the `semester` of many of the sections in this schedule do not match up with
        # the `semester` of the schedule
        curr_semester_schedule.sections.add(
            Course.objects.get(full_code="PSCI-498", semester="2019A").sections.get(code="001")
        )

        prev_semester_schedule = Schedule.objects.create(
            person=self.user, name="prev_semester_schedule", semester="2018C"
        )
        prev_semester_schedule.save()
        prev_semester_schedule.sections.add(
            Course.objects.get(full_code="PSCI-181", semester="2019A").sections.get(code="001")
        )

        response = self.client.get(
            reverse("courses-search", args=["current"]), {"search": "PSCI", "type": "auto"}
        )

        self.assertEqual(200, response.status_code)
        for course in response.data:
            self.assertIsInstance(course["recommendation_score"], float)


class SectionSearchTestCase(TestCase):
    def setUp(self):
        set_semester()
        create_mock_data("CIS-1200-001", TEST_SEMESTER)
        create_mock_data("CIS-1600-001", TEST_SEMESTER)
        create_mock_data("CIS-1200-201", TEST_SEMESTER)
        create_mock_data("PSCI-1810-001", TEST_SEMESTER)
        self.client = APIClient()

    def test_match_exact(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "CIS-1200-001"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-1200-001", res.data[0]["section_id"])

    def test_match_exact_spaces(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "CIS 1200 001"}
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("CIS-1200-001", res.data[0]["section_id"])

    def test_match_exact_nosep(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "PSCI1810001"}
        )
        self.assertEqual(res.status_code, 200)

        self.assertEqual(1, len(res.data))
        self.assertEqual("PSCI-1810-001", res.data[0]["section_id"])

    def test_match_full_course_nosep(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS1200"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-1200-001", res.data[0]["section_id"])

    def test_match_full_course_exact(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS-1200"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))
        self.assertEqual("CIS-1200-001", res.data[0]["section_id"])

    def test_match_full_course_space(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "PSCI 1810"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(1, len(res.data))

    def test_match_department(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "CIS"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(3, len(res.data))

    def test_match_lowercase(self):
        res = self.client.get(reverse("section-search", args=["current"]), {"search": "cis1200"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(res.data))

    def test_nomatch(self):
        res = self.client.get(
            reverse("section-search", args=["current"]), {"search": "123bdfsh3wq!@#"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(0, len(res.data))


class PreNGSSRequirementListTestCase(TestCase):
    def setUp(self):
        set_semester()
        get_or_create_course(
            "CIS", "120", "2012A"
        )  # dummy course to make sure we're filtering by semester
        self.course, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        self.course2, _ = get_or_create_course("CIS", "125", TEST_SEMESTER)
        self.department = Department.objects.get(code="CIS")

        self.req1 = PreNGSSRequirement(
            semester=TEST_SEMESTER, school="SAS", code="TEST1", name="Test 1"
        )
        self.req2 = PreNGSSRequirement(
            semester=TEST_SEMESTER, school="SAS", code="TEST2", name="Test 2"
        )
        self.req3 = PreNGSSRequirement(semester="XXXXX", school="SAS", code="TEST1", name="Test 1+")

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


class RestrictionListTestCase(TestCase):
    def setUp(self):
        set_semester()
        _, self.section, _, _ = get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        _, self.section2, _, _ = get_or_create_course_and_section("CIS-125-001", TEST_SEMESTER)
        self.department = Department.objects.get(code="CIS")

        self.restriction1 = NGSSRestriction.objects.create(
            restriction_type="ATTR",
            code="EMCI",
            description="SEAS CIS NonCIS Elective",
            inclusive=True,
        )
        # Fake restriction
        self.restriction2 = NGSSRestriction.objects.create(
            restriction_type="CAMP",
            code="PHILA",
            description="Philadelphia Campus",
            inclusive=True,
        )

        self.restriction1.sections.add(self.section)
        self.restriction2.sections.add(self.section)
        self.restriction2.sections.add(self.section2)
        self.client = APIClient()

    def test_restriction_route(self):
        response = self.client.get(reverse("restrictions-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(response.data))


class AttributeListTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        self.course2, _ = get_or_create_course("CIS", "125", TEST_SEMESTER)
        self.department = Department.objects.get(code="CIS")

        self.attr1 = Attribute.objects.create(
            code="EMCI",
            description="SEAS CIS NonCIS Elective",
            school="SEAS",
        )
        self.attr2 = Attribute.objects.create(
            code="WUFN",
            description="Wharton Finance Majo",
            school="WH",
        )
        self.attr1.courses.add(self.course)
        self.attr2.courses.add(self.course)
        self.attr2.courses.add(self.course2)
        self.client = APIClient()

    def test_attribute_route(self):
        response = self.client.get(reverse("attributes-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(response.data))
        self.assertEqual({res["code"] for res in response.data}, {"EMCI", "WUFN"})


class AttributeFilterTestCase(TestCase):
    def setUp(self):
        set_semester()
        # Courses (4)
        self.cis_120, _ = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.mgmt_117, _ = create_mock_data("MGMT-117-001", TEST_SEMESTER)
        self.econ_001, _ = create_mock_data("ECON-001-001", TEST_SEMESTER)
        self.anth_001, _ = create_mock_data("ANTH-001-001", TEST_SEMESTER)

        # Attributes
        self.wuom = Attribute.objects.create(
            code="WUOM", description="Wharton OIDD Operation", school="WH"
        )
        self.emci = Attribute.objects.create(
            code="EMCI", description="SEAS CIS NonCIS Elective", school="SEAS"
        )

        # Attach courses to attributes
        self.wuom.courses.add(self.mgmt_117)
        self.wuom.courses.add(self.econ_001)
        self.emci.courses.add(self.cis_120)
        self.emci.courses.add(self.econ_001)

        self.all_codes = {"CIS-120", "MGMT-117", "ECON-001", "ANTH-001"}

        self.client = APIClient()

    def test_no_attributes(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_single_attribute(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "WUOM"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"MGMT-117", "ECON-001"})

        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "ECON-001"})

    def test_multiple_overlapping_attributes(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "WUOM|EMCI"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"MGMT-117", "ECON-001", "CIS-120"})

    def test_nonexistent_attribute(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "LLLL"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(len(response.data), 0)

    def test_existent_and_nonexistent_attributes(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI|LLLL"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "ECON-001"})

    def test_and(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI*WUOM"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"ECON-001"})

    def test_and_nonexistent(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI*LLLL"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_and_or(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "(EMCI*WUOM)|EMCI"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "ECON-001"})

    def test_not(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "~EMCI"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"MGMT-117", "ANTH-001"})

    def test_not_nonexistent(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "~LLLL"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, self.all_codes)

    def test_and_not(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]),
            {"attributes": "~EMCI*WUOM"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"MGMT-117"})

    def test_and_or_not(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "(EMCI*WUOM)|~EMCI"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"ECON-001", "MGMT-117", "ANTH-001"})

    def test_and_or_nots(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]),
            {"attributes": "(~EMCI*WUOM)|~WUOM"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"CIS-120", "MGMT-117", "ANTH-001"})

    def test_demorgan(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]),
            {"attributes": "~EMCI*~WUOM"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual({res["id"] for res in response.data}, {"ANTH-001"})

    def test_empty_parens(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "()"}
        )
        self.assertEqual(response.status_code, 400)

    def test_partial_binary_op(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI|"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "|EMCI"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI*"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "*EMCI"}
        )
        self.assertEqual(response.status_code, 400)

    def test_partial_negation(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "~"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI|~"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI~"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unmatched_parens(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "(EMCI"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI)"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": ")EMCI("}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "(EMCI*(WUOM|LLLL)"}
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_chars(self):
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI,LLLL"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI&LLLL"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI^LLLL"}
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse("courses-search", args=[TEST_SEMESTER]), {"attributes": "EMCI+LLLL"}
        )
        self.assertEqual(response.status_code, 400)


class SectionListTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.math, self.math1 = create_mock_data("MATH-114-001", TEST_SEMESTER)
        self.client = APIClient()

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
        set_semester()
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
            json.dumps({"profile": {"phone": "19178286431"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["first_name"], "new_name")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")

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
                        "phone": "19178286431",
                        "push_notifications": True,
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "newname")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "newname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
                        "push_notifications": False,
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
                        "push_notifications": True,
                        "favorite_color": "blue",
                    },
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertFalse("favorite_color" in response.data["profile"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        self.assertFalse("middle_name" in response.data)
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
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
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "9178286431",
                        "push_notifications": True,
                    },
                }
            ),
            content_type="application/json",
        )
        response = self.client.put(
            reverse("user-view"),
            json.dumps({"profile": {"phone": "2128289349"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["phone"], "+12128289349")
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["phone"], "+12128289349")
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
                        "phone": "19178286431",
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
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "fname")
        self.assertEqual(response.data["last_name"], "lname")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
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
                {"profile": {"email": None, "phone": "19178286431", "push_notifications": True}}
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], None)
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "19178286431",
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
                        "phone": "19178286431",
                        "push_notifications": "True",
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
        self.assertTrue(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "jacob")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = self.client.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+19178286431")
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
                        "phone": "2128289349",
                        "push_notifications": "False",
                    }
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12128289349")
        self.assertFalse(response.data["profile"]["push_notifications"])
        self.assertEqual(response.data["username"], "murey")
        self.assertEqual(response.data["first_name"], "")
        self.assertEqual(response.data["last_name"], "")
        response = client2.get(reverse("user-view"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data["profile"]["email"], "example2@email.com")
        self.assertEqual(response.data["profile"]["phone"], "+12128289349")
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
                        "phone": "2128289349",
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
        set_semester()
        self.client = APIClient()

    def test_no_error(self):
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)

    def test_no_error_multiple_times(self):
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)

class CommentsTestCase(TestCase):
    def setUp(self):
        # Setup API
        self.client = APIClient()

        # Create Users
        self.client.force_login(User.objects.create_user(username="user1"))
        self.client.force_login(User.objects.create_user(username="user2"))
        self.client.force_login(User.objects.create_user(username="user3"))
        
        # Create Course & Reviews
        self._COURSE_CODE = "CIS-120-001"
        self.course, self.section = create_mock_data(self._COURSE_CODE, TEST_SEMESTER)

        # Create Base Level Comments
        self.id1 = self.create_comment("user1", self._COURSE_CODE, TEST_SEMESTER, None)
        self.id2 = self.create_comment("user2", self._COURSE_CODE, "2012A", None)

        # Reply to Comment
        self.id3 = self.create_comment("user3", self._COURSE_CODE, TEST_SEMESTER, self.id1)
        self.id4 = self.create_comment("user1", self._COURSE_CODE, TEST_SEMESTER, self.id1)

        # Add Vote Counts
        self.upvote("user1", self.id2)
        self.upvote("user1", self.id3)
        self.upvote("user2", self.id3)
        self.upvote("user3", self.id3)
        self.downvote("user1", self.id2)
        self.downvote("user2", self.id2)
    
    def get_comments(self, code, ordering):
        self.client.get(reverse("comment", kwargs={"course_code": code, "ordering": ordering}))

    def create_comment(self, username, code, semester, parent_id):
        self.client.post(reverse("comment", kwargs={"course_code": code, "username": username, "parent_id": parent_id}))

    def edit_comment(self, username, text, comment_id):
        self.client.put(reverse("comment", kwargs={"comment_id": comment_id, "text": text, "username": username}))

    def delete_comment(self, username, comment_id):
        self.client.delete(reverse("comment", kwargs={"comment_id": comment_id, "username": username}))

    def upvote(self, username, comment_id):
        self.client.post(reverse("upvote", kwargs={"comment_id": comment_id, "username": username}))

    def downvote(self, username, comment_id):
        self.client.post(reverse("downvote", kwargs={"comment_id": comment_id, "username": username}))
    
    
    def test_comment_count(self):
        self.assertEqual(len(self.get_comments(self._COURSE_CODE)), 3)
    
    def test_time_ordering_new(self):
        comments = self.get_comments(self._COURSE_CODE, "new")
        self.assertEqual(len(comments), 4)
        self.assertEqual(comments[0].id, self.id2)
        self.assertEqual(comments[1].id, self.id1)
        self.assertEqual(comments[2].id, self.id3)
        self.assertEqual(comments[3].id, self.id4)

    def test_time_ordering_old(self):
        comments = self.get_comments(self._COURSE_CODE, "old")
        self.assertEqual(len(comments), 4)
        self.assertEqual(comments[0].id, self.id1)
        self.assertEqual(comments[1].id, self.id3)
        self.assertEqual(comments[2].id, self.id4)
        self.assertEqual(comments[3].id, self.id2)
        
    def test_popularity_ordering(self):
        comments = self.get_comments(self._COURSE_CODE, "top")
        self.assertEqual(len(comments), 4)
        self.assertEqual(comments[0].id, self.id2)
        self.assertEqual(comments[1].id, self.id1)
        self.assertEqual(comments[2].id, self.id3)
        self.assertEqual(comments[3].id, self.id4)

    def test_delete_base(self):
        self.delete_comment("user2", self.id2)
        comments = self.get_comments(self._COURSE_CODE, "new")
        self.assertEqual(len(comments), 3)

    def test_delete_base_with_reply(self):
        self.delete_comment("user1", self.id1)
        comments = self.get_comments(self._COURSE_CODE, "new")
        self.assertEqual(len(comments), 4)
        for comment in comments:
            if comment.id == self.id1:
                self.assertTrue(comment.text, "This comment has been removed.")
                return
        self.assertFalse()
    
    def test_delete_reply(self):
        self.delete_comment("user1", self.id4)
        comments = self.get_comments(self._COURSE_CODE, "new")
        self.assertEqual(len(comments), 3)
        self.assertFalse()

    def test_new_upvote_downvote(self):
        self.upvote("user2", self.id4)
        comments = self.get_comments(self._COURSE_CODE, "new")
        for comment in comments:
            if comment.id == self.id4:
                self.assertTrue(comment.vote_count, 1)
                return
        self.assertFalse()

    def test_old_upvote_downvote(self):
        self.upvote("user2", self.id3)
        comments = self.get_comments(self._COURSE_CODE, "new")
        for comment in comments:
            if comment.id == self.id3:
                self.assertTrue(comment.vote_count, 3)
                return
        self.assertFalse()

    def test_switch_votes(self):
        self.upvote("user2", self.id2)
        comments = self.get_comments(self._COURSE_CODE, "new")
        for comment in comments:
            if comment.id == self.id2:
                self.assertTrue(comment.vote_count, 2)
                return
        self.assertFalse()