from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.management.commands.populate_prereqs import (
    build_prereq_rule,
    parse_course_code,
    parse_prereq_expression,
    parse_prereq_pairs,
    populate_prereqs_from_scrape,
    resolve_prereq_course,
)
from courses.models import Course
from courses.util import get_prerequisite_chain, invalidate_current_semester_cache
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


def parse_rule(text):
    """Parse class notes into a rule, treating every course as present in the database."""
    return build_prereq_rule(parse_prereq_expression(text), lambda dept, code: f"{dept}-{code}")


class ParsePrereqRuleTestCase(TestCase):
    def test_or_alternatives(self):
        self.assertEqual(
            parse_rule("Prerequisite: BIOL 2810 OR BIOL 2010 OR BIOL 2210"),
            {"or": ["BIOL-2810", "BIOL-2010", "BIOL-2210"]},
        )

    def test_or_binds_tighter_than_and(self):
        self.assertEqual(
            parse_rule("Prerequisites: CHEM 2410 OR CHEM 2411 AND CHEM 2420 OR CHEM 2421"),
            {"and": [{"or": ["CHEM-2410", "CHEM-2411"]}, {"or": ["CHEM-2420", "CHEM-2421"]}]},
        )

    def test_parentheses_and_brackets_group(self):
        expected = {"and": ["ECON-2100", {"or": ["ECON-2200", "FNCE-1010"]}, "MATH-1400"]}
        self.assertEqual(
            parse_rule("Prerequisites: ECON 2100 AND (ECON 2200 OR FNCE 1010) AND MATH 1400"),
            expected,
        )
        self.assertEqual(
            parse_rule("Prerequisites: ECON 2100 and [ECON 2200 or FNCE 1010] and MATH 1400."),
            expected,
        )

    def test_department_before_parenthesis_carries_in(self):
        self.assertEqual(
            parse_rule("Prerequisite: MATH (1400 or 1070) and ECON 2100"),
            {"and": [{"or": ["MATH-1400", "MATH-1070"]}, "ECON-2100"]},
        )

    def test_comma_lists_take_the_final_connector(self):
        self.assertEqual(
            parse_rule("Prerequisites: ECON 2100, 2200, and 2300"),
            {"and": ["ECON-2100", "ECON-2200", "ECON-2300"]},
        )
        self.assertEqual(
            parse_rule("Prerequisite: PSYC 1210, or PSYC 1230, or PSYC 1530"),
            {"or": ["PSYC-1210", "PSYC-1230", "PSYC-1530"]},
        )

    def test_slash_is_an_alternative(self):
        self.assertEqual(
            parse_rule("The prerequisite for this course is REAL/FNCE 7210."),
            {"or": ["REAL-7210", "FNCE-7210"]},
        )

    def test_slash_between_numbers_is_an_alternative_but_not_between_words(self):
        self.assertEqual(
            parse_rule("Prerequisite: PSYC 1530/2300 and CIS 1200. Pass/Fail not an option."),
            {"and": [{"or": ["PSYC-1530", "PSYC-2300"]}, "CIS-1200"]},
        )
        self.assertEqual(
            parse_rule("Prerequisite: CIS 1200 and instructor/department permission"),
            {"and": ["CIS-1200", {"text": "instructor department permission"}]},
        )

    def test_course_titles_are_dropped(self):
        self.assertEqual(
            parse_rule(
                "Prerequisites: MATH 2400, Calculus, Part III or Math 2600, Honors Calculus."
            ),
            {"or": ["MATH-2400", "MATH-2600"]},
        )

    def test_non_course_alternatives_are_kept_as_text(self):
        self.assertEqual(
            parse_rule(
                "Registration required for LEC and REC. Prerequisites: MATH 1400, Calculus, "
                "Part I OR Placement score of 24+ OR instructor permission."
            ),
            {
                "or": [
                    "MATH-1400",
                    {"text": "Placement score of 24+"},
                    {"text": "instructor permission"},
                ]
            },
        )

    def test_keyword_after_the_course(self):
        self.assertEqual(
            parse_rule(
                "Successful prior completion of WH 1010 is a pre-requisite for enrollment in "
                "WH 2010."
            ),
            "WH-1010",
        )

    def test_only_prerequisite_sentences_are_read(self):
        self.assertEqual(
            parse_rule(
                "Grad students should enroll in REES 5183. Prerequisites: ECON 0100 and 0200 "
                "Antirequisite: ECON 4510"
            ),
            {"and": ["ECON-0100", "ECON-0200"]},
        )
        self.assertIsNone(parse_rule("ARCH 5990 is a co-requisite for this class."))

    def test_asides_and_grade_qualifiers_are_ignored(self):
        self.assertEqual(
            parse_rule(
                "Prerequisite: ECON 0100 (formerly ECON 001) with a grade of C or better and "
                "MATH 1300 (may be taken concurrently)"
            ),
            {"and": ["ECON-0100", "MATH-1300"]},
        )

    def test_unresolved_courses_are_dropped(self):
        rule = build_prereq_rule(
            parse_prereq_expression("Prerequisite: CIS 1200 or CIS 9999 and MATH 9999"),
            lambda dept, code: None if code == "9999" else f"{dept}-{code}",
        )
        self.assertEqual(rule, "CIS-1200")

    def test_rule_without_courses_is_none(self):
        self.assertIsNone(parse_rule("Prerequisite: permission of instructor"))
        self.assertIsNone(parse_rule(""))


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

    def test_stores_prerequisite_rule(self):
        other, _ = create_mock_data("CIS-1600-001", TEST_SEMESTER)
        records = [dict(self.records[0], clssnotes="Prerequisite: CIS 1200 or CIS 1600")]
        populate_prereqs_from_scrape([TEST_SEMESTER], records)
        self.course.refresh_from_db()
        self.assertEqual(self.course.prerequisite_rule, {"or": ["CIS-1200", "CIS-1600"]})
        self.assertEqual(self.course.prerequisite_courses.count(), 2)

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

    def test_detail_includes_prerequisite_chain(self):
        Course.objects.filter(id=self.course.id).update(prerequisite_rule="CIS-1200")
        self.assertEqual(
            self.detail("CIS-1210")["prerequisite_chain"],
            {
                "CIS-1210": {"title": self.course.title, "prerequisite_rule": "CIS-1200"},
                "CIS-1200": {"title": self.prereq.title, "prerequisite_rule": None},
            },
        )

    def test_fields_are_read_only_lists(self):
        data = self.detail("CIS-1210")
        self.assertIsInstance(data["prerequisite_courses"], list)
        self.assertIsInstance(data["dependent_courses"], list)
        self.assertEqual(Course.objects.get(full_code="CIS-1210").prerequisite_courses.count(), 1)


class PrerequisiteChainTestCase(TestCase):
    def setUp(self):
        set_semester()
        for code in ["CIS-1100", "CIS-1200", "CIS-1600", "CIS-1210", "CIS-3200"]:
            create_mock_data(f"{code}-001", TEST_SEMESTER)
        self.set_rule("CIS-1200", "CIS-1100")
        self.set_rule("CIS-1210", {"and": ["CIS-1200", "CIS-1600"]})
        self.set_rule("CIS-3200", {"or": ["CIS-1210", {"text": "instructor permission"}]})

    def set_rule(self, full_code, rule):
        Course.objects.filter(full_code=full_code).update(prerequisite_rule=rule)

    def test_follows_rules_transitively(self):
        chain = get_prerequisite_chain("CIS-3200")
        self.assertEqual(set(chain), {"CIS-3200", "CIS-1210", "CIS-1200", "CIS-1600", "CIS-1100"})
        self.assertEqual(chain["CIS-1200"]["prerequisite_rule"], "CIS-1100")
        self.assertIsNone(chain["CIS-1100"]["prerequisite_rule"])

    def test_cycles_terminate(self):
        self.set_rule("CIS-1100", "CIS-3200")
        self.assertEqual(len(get_prerequisite_chain("CIS-3200")), 5)

    def test_prefers_the_most_recent_rule(self):
        old, _ = create_mock_data("CIS-1200-001", "2023C")
        Course.objects.filter(id=old.id).update(prerequisite_rule="CIS-1600")
        self.assertEqual(
            get_prerequisite_chain("CIS-1200")["CIS-1200"]["prerequisite_rule"], "CIS-1100"
        )
        Course.objects.filter(full_code="CIS-1200", semester=TEST_SEMESTER).update(
            prerequisite_rule=None
        )
        self.assertEqual(
            get_prerequisite_chain("CIS-1200")["CIS-1200"]["prerequisite_rule"], "CIS-1600"
        )
