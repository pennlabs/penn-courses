from decimal import Decimal
from os import path

from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Major, Minor
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees
from degree.utils.parse_path_audit import find_block, parse_audit, save_component, save_parsed_audit


FIXTURES = path.join(path.dirname(path.abspath(__file__)), "fixtures")
TEST_SEMESTER = "2023C"


def load_audit(name):
    with open(path.join(FIXTURES, name)) as f:
        return f.read()


class ComponentIngestTest(TestCase):
    """
    A Degree is a whole audit. A Major or Minor added on top of one contributes only its own
    block: the rest of the audit it came from describes a degree the student is not pursuing.
    """

    def parse(self, fixture, **kw):
        degree = Degree(**kw)
        parsed = parse_audit(load_audit(fixture), degree)
        degree.year = parsed.catalog_year
        return degree, parsed

    def test_a_major_carries_only_its_own_block(self):
        degree, parsed = self.parse(
            "MATH-BA-GEN.xml", program="AU_BA", degree="BA", major="MATH", concentration="GEN"
        )
        block = find_block(parsed, "MAJOR")
        major = Major(
            program_code="MATH-BA-GEN",
            code=block.req_value,
            name="Mathematics",
            concentration="GEN",
            year=parsed.catalog_year,
        )
        save_component(major, parsed, block)

        blocks = {rule.block_value for rule in major.rules.all()}
        self.assertEqual(blocks, {"MATH"})
        self.assertEqual(major.credits, Decimal("13"))

        # the College's general education blocks are not inherited
        titles = {rule.title for rule in major.rules.all()}
        self.assertNotIn("Arts and Sciences 27 CU Requirement", titles)

    def test_a_minor_carries_only_its_own_block(self):
        # A minor's audit wraps its MINOR block in a full BA degree, which is discarded.
        placeholder = Degree(program="AU_BA", degree="BA", major="MATH", year=0)
        parsed = parse_audit(load_audit("MATH-MINOR.xml"), placeholder)
        block = find_block(parsed, "MINOR")
        self.assertIsNotNone(block)
        self.assertEqual(block.req_value, "MATH")

        minor = Minor(
            program_code="MATH-MINOR",
            code=block.req_value,
            name="Mathematics",
            year=parsed.catalog_year,
        )
        save_component(minor, parsed, block)
        self.assertEqual(minor.credits, Decimal("7"))
        self.assertEqual({r.block_type for r in minor.rules.all()}, {"MINOR"})

    def test_minor_rules_are_standalone_so_they_share_freely(self):
        # Minor blocks are marked STANDALONEBLOCK, which the parser reads as ANYBLOCK.
        placeholder = Degree(program="AU_BA", degree="BA", major="CSCI", year=0)
        parsed = parse_audit(load_audit("CSCI-MINOR.xml"), placeholder)
        block = find_block(parsed, "MINOR")
        leaves = [
            r
            for r in parsed.rules
            if r.q and r.block_type == "MINOR" and r.block_value == block.req_value
        ]
        self.assertTrue(leaves)
        for rule in leaves:
            self.assertIn({"kind": "ANYBLOCK", "value": None}, rule.share_targets)


class SecondMajorPlanTest(TestCase):
    """
    A Mechanical Engineering BSE with a second major in Math and a minor in Computer Science.
    """

    def setUp(self):
        for code in ["MATH-1400", "MATH-2400", "MATH-3140", "CIS-1200"]:
            get_or_create_course_and_section(f"{code}-001", TEST_SEMESTER)

        meam = Degree(
            program="EU_BSE",
            degree="BSE",
            major="MEAM",
            concentration="GEN",
            major_name="Mech Engr & Appl Mechanics",
        )
        parsed = parse_audit(load_audit("MEAM-BSE-GEN.xml"), meam)
        meam.year = parsed.catalog_year
        save_parsed_audit(parsed, meam)
        self.meam = meam

        math_degree = Degree(program="AU_BA", degree="BA", major="MATH", concentration="GEN")
        math_parsed = parse_audit(load_audit("MATH-BA-GEN.xml"), math_degree)
        block = find_block(math_parsed, "MAJOR")
        self.math = Major(
            program_code="MATH-BA-GEN",
            code="MATH",
            name="Mathematics",
            concentration="GEN",
            year=math_parsed.catalog_year,
        )
        save_component(self.math, math_parsed, block)

        placeholder = Degree(program="AU_BA", degree="BA", major="CSCI", year=0)
        minor_parsed = parse_audit(load_audit("CSCI-MINOR.xml"), placeholder)
        minor_block = find_block(minor_parsed, "MINOR")
        self.cis_minor = Minor(
            program_code="CSCI-MINOR",
            code="CSCI",
            name="Computer Science",
            year=minor_parsed.catalog_year,
        )
        save_component(self.cis_minor, minor_parsed, minor_block)

        person = get_user_model().objects.create_user(username="t", password="x")
        self.plan = DegreePlan.objects.create(name="MEAM + Math + CIS minor", person=person)
        self.plan.degrees.add(meam)
        self.plan.majors.add(self.math)
        self.plan.minors.add(self.cis_minor)

    def allocate(self, full_code):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        return allocate_rules(
            full_code, rules_per_degree, rule_to_degree, double_counts, satisfied_rules=set()
        )

    def test_all_three_components_contribute_rules(self):
        rules_per_degree, _, _ = map_rules_and_degrees(self.plan)
        owners = {type(owner).__name__ for owner in rules_per_degree}
        self.assertEqual(owners, {"Degree", "Major", "Minor"})

    def test_the_second_major_does_not_drag_in_college_requirements(self):
        rules_per_degree, _, _ = map_rules_and_degrees(self.plan)
        blocks = {rule.block_value for rules in rules_per_degree.values() for rule in rules}
        self.assertNotIn("U-GE-FND", blocks)
        self.assertNotIn("U-GE-SCTR", blocks)
        self.assertIn("MEAM", blocks)
        self.assertIn("MATH", blocks)
        self.assertIn("CSCI", blocks)

    def test_a_course_can_count_for_the_degree_and_the_second_major(self):
        # MATH 1400 is Calculus I for MEAM and part of "Calculus I and II" for the Math major.
        selected, _, legal = self.allocate("MATH-1400")
        blocks = {rule.block_value for rule in selected}
        self.assertIn("MEAM", blocks)
        self.assertIn("MATH", blocks)
        self.assertTrue(legal)

    def test_a_course_only_the_degree_needs_stays_with_the_degree(self):
        selected, _, legal = self.allocate("MATH-2400")
        self.assertEqual({rule.block_value for rule in selected}, {"MEAM"})
        self.assertTrue(legal)

    def test_a_minor_course_is_legal_alongside_the_rest(self):
        selected, _, legal = self.allocate("CIS-1200")
        self.assertIn("CSCI", {rule.block_value for rule in selected})
        self.assertTrue(legal)
