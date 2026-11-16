from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase

from degree.data.dual_programs import load
from degree.models import Degree, DegreePlan, DualProgram, Rule
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees
from degree.utils.double_counts import get_degree_trees

from .test_composition import course


WRITING = repr(Q(department__code="WRIT", code__lte="0991"))
ARTS_AND_SCIENCES = repr(Q(department__code__in=["ECON", "HIST"]))


def college_degree(major, year):
    degree = Degree.objects.create(program="AU_BA", degree="BA", major=major, year=year)
    ba = Rule.objects.create(
        title="Degree in Bachelor of Arts", block_type="DEGREE", block_value="BA"
    )
    Rule.objects.create(
        title="Arts and Sciences 30 CU Requirement",
        parent=ba,
        q=ARTS_AND_SCIENCES,
        credits=30,
        block_type="DEGREE",
        block_value="BA",
    )
    foundations = Rule.objects.create(
        title="General Education, Foundations", block_type="OTHER", block_value="U-GE-FND"
    )
    Rule.objects.create(
        title="Writing Course",
        parent=foundations,
        q=WRITING,
        num=1,
        block_type="OTHER",
        block_value="U-GE-FND",
    )
    degree.rules.add(ba, foundations)
    return degree


def inst(year):
    return Degree.objects.get(program="AU_BA", degree="BA", major="INST", year=year)


def leaves(degree):
    return {rule.title: rule for rule in get_degree_trees([degree])[degree] if rule.q}


class HuntsmanDegreeTest(TestCase):
    def test_built_for_each_college_catalog_year(self):
        college_degree("ECON", 2025)
        college_degree("HIST", 2026)
        Degree.objects.create(program="WU_BS", degree="BS", major="WH", year=2027)
        load()
        self.assertEqual(
            sorted(Degree.objects.filter(major="INST").values_list("year", flat=True)),
            [2025, 2026],
        )
        self.assertEqual(DualProgram.objects.get(code="HUNTSMAN").left_allowed_majors, ["INST"])

    def test_major_follows_the_worksheet(self):
        college_degree("ECON", 2026)
        load()
        rules = leaves(inst(2026))
        self.assertEqual(rules["Advanced Language"].credits, 4)
        self.assertEqual(rules["Area Studies"].credits, 3)
        self.assertEqual(rules["International Studies"].credits, 2)
        self.assertEqual(rules["International Business"].credits, 2)
        self.assertEqual(rules["International Studies or Business"].credits, 1)
        self.assertIn("INSP-1001", rules["Huntsman First-Year Seminar"].q)
        self.assertIn("MGMT-4090", rules["MGMT 4090"].q)
        self.assertIn("INSP-4999", rules["Senior Project or Thesis"].q)

    def test_college_requirements_reuse_path_and_drop_covered_sectors(self):
        college_degree("ECON", 2026)
        load()
        rules = leaves(inst(2026))
        self.assertEqual(rules["Writing Course"].q, WRITING)
        arts_and_sciences = rules["Arts and Sciences 24 CU Requirement"]
        self.assertEqual(arts_and_sciences.credits, 24)
        self.assertIn("INSP", arts_and_sciences.q)
        self.assertIn("ECON", arts_and_sciences.q)
        self.assertNotIn("Sector 1: Society", rules)
        self.assertNotIn("Sector 4: Humanities and Social Sciences", rules)
        self.assertIn("Sector 2: History and Tradition", rules)

    def test_reloading_keeps_the_same_rules(self):
        college_degree("ECON", 2026)
        load()
        before = {rule.id for rule in get_degree_trees([inst(2026)])[inst(2026)]}
        load()
        after = {rule.id for rule in get_degree_trees([inst(2026)])[inst(2026)]}
        self.assertEqual(before, after)
        self.assertEqual(Degree.objects.filter(major="INST").count(), 1)


def wharton_degree(year):
    """A Wharton BS with one leaf in each block Path's audit has."""
    degree = Degree.objects.create(
        program="WU_BS", degree="BS", major="FNCE", concentration=None, year=year
    )

    def block(title, block_type, block_value, leaves):
        root = Rule.objects.create(title=title, block_type=block_type, block_value=block_value)
        for leaf_title, q in leaves:
            Rule.objects.create(
                title=leaf_title,
                parent=root,
                q=repr(q),
                credits=1,
                block_type=block_type,
                block_value=block_value,
            )
        degree.rules.add(root)

    block(
        "First-Year Foundations",
        "OTHER",
        "U-WFYF",
        [
            ("Introductory Economics", Q(full_code="BEPP-1000")),
            ("Critical Writing Seminar", Q(full_code="WRIT-0020")),
        ],
    )
    block(
        "Business Fundamentals",
        "OTHER",
        "U-WBUS",
        [
            ("Senior Capstone", Q(attributes__code__in=["WUCP"])),
            ("Global Economy, Business and Society", Q(attributes__code__in=["WUGE"])),
            ("Corporate Finance", Q(full_code="FNCE-1000")),
        ],
    )
    block("Liberal Arts", "OTHER", "U-WLAS", [("Humanities", Q(attributes__code__in=["WUHM"]))])
    block(
        "Business Breadth", "OTHER", "U-WBBR2", [("Business Breadth", Q(department__code="FNCE"))]
    )
    block(
        "Finance Concentration",
        "MAJOR",
        "FNCE",
        [("Finance Electives", Q(department__code="FNCE"))],
    )
    return degree


class HuntsmanWhartonTest(TestCase):
    def setUp(self):
        college_degree("ECON", 2026)
        self.wharton = wharton_degree(2026)
        load()
        self.plan = DegreePlan.objects.create(
            name="huntsman",
            person=get_user_model().objects.create_user(username="h", password="x"),
            dual_program=DualProgram.objects.get(code="HUNTSMAN"),
        )
        self.plan.degrees.add(inst(2026), self.wharton)
        self.plan_rules = map_rules_and_degrees(self.plan)

    def selected(self, full_code):
        selected, _, _ = allocate_rules(
            full_code,
            self.plan_rules.rules_per_component,
            self.plan_rules.rule_to_component,
            self.plan_rules.double_counts,
            satisfied_rules=set(),
            policy=self.plan_rules.composition.policy,
        )
        return {rule.title for rule in selected}

    def test_drops_what_the_college_degree_covers(self):
        titles = {
            rule.title
            for rule, component in self.plan_rules.rule_to_component.items()
            if component.program == "WU_BS"
        }
        self.assertEqual(
            titles,
            {"Introductory Economics", "Corporate Finance", "Finance Electives", "Senior Capstone"},
        )

    def test_mgmt_4090_is_both_capstones(self):
        course("MGMT-4090")
        self.assertEqual(self.selected("MGMT-4090"), {"MGMT 4090", "Senior Capstone"})

    def test_concentration_course_is_not_also_international_business(self):
        course("FNCE-2190", attributes=["WUIS"])
        selected = self.selected("FNCE-2190")
        self.assertIn("Finance Electives", selected)
        self.assertFalse(selected & {"International Business", "International Studies or Business"})

    def test_international_business_still_shares_outside_the_concentration(self):
        course("FNCE-1000", attributes=["WUIS"])
        self.assertEqual(
            self.selected("FNCE-1000"), {"Corporate Finance", "International Business"}
        )
