from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.management.commands.populate_prereqs import (
    parse_course_code,
    parse_prereq_pairs,
    populate_prereqs_from_scrape,
    resolve_prereq_course,
)
from courses.models import Course
from courses.util import invalidate_current_semester_cache
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2024C"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class ParsePrereqPairsTestCase(TestCase):
    def test_department_carries_over_to_bare_numbers(self):
        pairs = parse_prereq_pairs("Prerequisite: CIS 1200, 1600 and MATH-1400.")
        self.assertEqual(pairs, {("CIS", "1200"), ("CIS", "1600"), ("MATH", "1400")})

    def test_html_tags_are_stripped(self):
        pairs = parse_prereq_pairs("<p>Prereq: <b>CIS 1210</b> or <b>CIS-1600</b></p>")
        self.assertEqual(pairs, {("CIS", "1210"), ("CIS", "1600")})

    def test_lower_case_number_suffix_is_normalized(self):
        self.assertEqual(parse_prereq_pairs("Prereq: MATH 1400a"), {("MATH", "1400A")})

    def test_bare_number_without_department_is_ignored(self):
        self.assertEqual(parse_prereq_pairs("Section 001 meets in 2024"), set())

    def test_lower_case_words_are_not_departments(self):
        self.assertEqual(
            parse_prereq_pairs("Class starts in 2026. Prereq: CIS 1200"), {("CIS", "1200")}
        )

    def test_bare_number_after_a_sentence_break_does_not_inherit_department(self):
        pairs = parse_prereq_pairs("Prerequisite: CIS 1200. Class starts August 24, 2026.")
        self.assertEqual(pairs, {("CIS", "1200")})

    def test_bare_numbers_in_a_list_inherit_department(self):
        pairs = parse_prereq_pairs("Prereq: MATH 1400, 1410 or 1610 and PHYS 0150")
        self.assertEqual(
            pairs, {("MATH", "1400"), ("MATH", "1410"), ("MATH", "1610"), ("PHYS", "0150")}
        )

    def test_empty_text(self):
        self.assertEqual(parse_prereq_pairs(""), set())
        self.assertEqual(parse_prereq_pairs(None), set())


class ParseCourseCodeTestCase(TestCase):
    def test_accepts_space_and_dash_forms(self):
        self.assertEqual(parse_course_code("CIS 1200"), ("CIS", "1200"))
        self.assertEqual(parse_course_code("cis-1200"), ("CIS", "1200"))

    def test_rejects_department_only(self):
        with self.assertRaises(ValueError):
            parse_course_code("CIS")


class ResolvePrereqCourseTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.new, _ = create_mock_data("CIS-1200-001", "2024C")
        self.old, _ = create_mock_data("CIS-1200-001", "2023C")

    def test_prefers_same_semester(self):
        self.assertEqual(resolve_prereq_course("CIS", "1200", "2024C"), self.new.primary_listing)

    def test_falls_back_to_most_recent_earlier_semester(self):
        self.assertEqual(resolve_prereq_course("CIS", "1200", "2024A"), self.old.primary_listing)

    def test_falls_back_to_any_offering_when_nothing_earlier(self):
        self.assertEqual(resolve_prereq_course("CIS", "1200", "2022A"), self.new.primary_listing)

    def test_unknown_course_is_none(self):
        self.assertIsNone(resolve_prereq_course("CIS", "9999", "2024C"))


class PopulatePrereqsTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.prereq, _ = create_mock_data("CIS-1200-001", TEST_SEMESTER)
        self.course, self.section = create_mock_data("CIS-1210-001", TEST_SEMESTER)
        self.records = [
            {
                "course_code": "CIS 1210",
                "crn": str(self.section.crn),
                "clssnotes": "Prerequisite: CIS 1200. Also mentions CIS 1210 itself.",
            }
        ]

    def test_links_prerequisites_from_scrape(self):
        stats = populate_prereqs_from_scrape([TEST_SEMESTER], self.records)
        self.assertEqual(stats["courses_touched"], 1)
        self.assertEqual(stats["created_links"], 1)
        self.assertEqual(stats["unresolved_pairs"], 0)
        self.assertEqual(
            list(self.course.prerequisite_courses.values_list("full_code", flat=True)),
            ["CIS-1200"],
        )
        self.assertEqual(
            list(self.prereq.dependent_courses.values_list("full_code", flat=True)),
            ["CIS-1210"],
        )

    def test_self_reference_is_skipped(self):
        populate_prereqs_from_scrape([TEST_SEMESTER], self.records)
        self.assertNotIn(self.course, self.course.prerequisite_courses.all())

    def test_dry_run_writes_nothing(self):
        stats = populate_prereqs_from_scrape([TEST_SEMESTER], self.records, dry_run=True)
        self.assertEqual(stats["created_links"], 1)
        self.assertEqual(self.course.prerequisite_courses.count(), 0)

    def test_unmatched_crn_is_counted_as_missing(self):
        records = [dict(self.records[0], crn="000000")]
        stats = populate_prereqs_from_scrape([TEST_SEMESTER], records)
        self.assertEqual(stats["missing_courses"], 1)
        self.assertEqual(stats["courses_touched"], 0)

    def test_clear_existing_replaces_links(self):
        other, _ = create_mock_data("MATH-1400-001", TEST_SEMESTER)
        self.course.prerequisite_courses.add(other)
        populate_prereqs_from_scrape([TEST_SEMESTER], self.records, clear_existing=True)
        self.assertEqual(
            list(self.course.prerequisite_courses.values_list("full_code", flat=True)),
            ["CIS-1200"],
        )

    def test_without_clear_existing_links_accumulate(self):
        other, _ = create_mock_data("MATH-1400-001", TEST_SEMESTER)
        self.course.prerequisite_courses.add(other)
        populate_prereqs_from_scrape([TEST_SEMESTER], self.records)
        self.assertEqual(self.course.prerequisite_courses.count(), 2)


class CourseDetailPrereqFieldsTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.prereq, _ = create_mock_data("CIS-1200-001", TEST_SEMESTER)
        self.course, _ = create_mock_data("CIS-1210-001", TEST_SEMESTER)
        self.course.prerequisite_courses.add(self.prereq)
        self.client = APIClient()

    def detail(self, full_code):
        response = self.client.get(
            reverse("courses-detail", kwargs={"semester": "all", "full_code": full_code})
        )
        self.assertEqual(200, response.status_code)
        return response.data

    def test_detail_lists_prerequisites_and_dependents(self):
        self.assertEqual(self.detail("CIS-1210")["prerequisite_courses"], ["CIS-1200"])
        self.assertEqual(self.detail("CIS-1210")["dependent_courses"], [])
        self.assertEqual(self.detail("CIS-1200")["dependent_courses"], ["CIS-1210"])
        self.assertEqual(self.detail("CIS-1200")["prerequisite_courses"], [])

    def test_fields_are_read_only_lists(self):
        data = self.detail("CIS-1210")
        self.assertIsInstance(data["prerequisite_courses"], list)
        self.assertIsInstance(data["dependent_courses"], list)
        self.assertEqual(Course.objects.get(full_code="CIS-1210").prerequisite_courses.count(), 1)
