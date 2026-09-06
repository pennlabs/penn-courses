from collections import defaultdict
from decimal import Decimal
from itertools import combinations
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
    A Degree is a whole audit. A major or minor added on top of one contributes only its own
    block: the rest of the audit it came from describes a degree the student is not pursuing.
    """

    def test_a_major_carries_only_its_own_block(self):
        degree = Degree(program="AU_BA", degree="BA", major="MATH", concentration="GEN")
        parsed = parse_audit(load_audit("MATH-BA-GEN.xml"), degree)
        block = find_block(parsed, "MAJOR")

        major = Major(
            program_code="MATH-BA-GEN",
            code=block.req_value,
            name="Mathematics",
            concentration="GEN",
            year=parsed.catalog_year,
        )
        save_component(major, parsed, block)

        self.assertEqual({rule.block_value for rule in major.rules.all()}, {"MATH"})
        self.assertEqual(major.credits, Decimal("13"))

    def test_a_minor_carries_only_its_own_block_and_shares_freely(self):
        # A minor's audit wraps its MINOR block in a full BA degree, which is discarded. The
        # block is marked STANDALONEBLOCK, so its rules double count with everything.
        placeholder = Degree(program="AU_BA", degree="BA", major="CSCI", year=0)
        parsed = parse_audit(load_audit("CSCI-MINOR.xml"), placeholder)
        block = find_block(parsed, "MINOR")

        minor = Minor(
            program_code="CSCI-MINOR",
            code=block.req_value,
            name="Computer Science",
            year=parsed.catalog_year,
        )
        save_component(minor, parsed, block)

        self.assertEqual({rule.block_type for rule in minor.rules.all()}, {"MINOR"})
        self.assertEqual(minor.credits, Decimal("6"))
        for rule in minor.rules.all():
            if rule.q:
                self.assertIn({"kind": "ANYBLOCK", "value": None}, rule.share_targets)


class SecondMajorPlanTest(TestCase):
    """
    A Mechanical Engineering BSE with a second major in Math.
    """

    def setUp(self):
        for code in ["MATH-1400", "MATH-2400"]:
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

        math_degree = Degree(program="AU_BA", degree="BA", major="MATH", concentration="GEN")
        math_parsed = parse_audit(load_audit("MATH-BA-GEN.xml"), math_degree)
        self.math = Major(
            program_code="MATH-BA-GEN",
            code="MATH",
            name="Mathematics",
            concentration="GEN",
            year=math_parsed.catalog_year,
        )
        save_component(self.math, math_parsed, find_block(math_parsed, "MAJOR"))

        person = get_user_model().objects.create_user(username="t", password="x")
        self.plan = DegreePlan.objects.create(name="MEAM + Math", person=person)
        self.plan.degrees.add(meam)
        self.plan.majors.add(self.math)

    def test_the_plan_is_the_degree_plus_the_major_alone(self):
        rules_per_degree, _, _ = map_rules_and_degrees(self.plan)

        self.assertEqual({type(owner).__name__ for owner in rules_per_degree}, {"Degree", "Major"})
        blocks = {rule.block_value for rules in rules_per_degree.values() for rule in rules}
        self.assertIn("MEAM", blocks)
        self.assertIn("MATH", blocks)
        # the College's requirements belong to a degree this student is not pursuing
        self.assertNotIn("U-GE-FND", blocks)
        self.assertNotIn("U-GE-SCTR", blocks)

    def test_a_course_counts_for_the_degree_and_the_second_major(self):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        selected, _, legal = allocate_rules(
            "MATH-1400", rules_per_degree, rule_to_degree, double_counts, satisfied_rules=set()
        )

        self.assertEqual({rule.block_value for rule in selected}, {"MEAM", "MATH"})
        self.assertTrue(legal)

    def test_no_component_contributes_two_rules_that_cannot_share(self):
        """
        allocate_rules walks each component and unions the results, and every pass reaches
        into the others to find what its chosen rule may share with. A pass that kept those
        reached-into rules could union with another pass into a pair of one component's
        rules that may not share, flagging the course as illegally double counted.
        """
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)

        for full_code in ["MATH-1400", "MATH-2400"]:
            selected, _, legal = allocate_rules(
                full_code,
                rules_per_degree,
                rule_to_degree,
                double_counts,
                satisfied_rules=set(),
            )
            by_component = defaultdict(list)
            for rule in selected:
                by_component[rule_to_degree[rule]].append(rule)

            for component, rules in by_component.items():
                for first, second in combinations(rules, 2):
                    self.assertIn(
                        second,
                        double_counts.get(first, set()),
                        f"{full_code}: {component} contributed two rules that cannot share",
                    )
            self.assertTrue(legal, f"{full_code} was flagged illegal")
