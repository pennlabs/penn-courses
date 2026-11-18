from django.contrib.auth import get_user_model
from django.test import TestCase

from degree.data.premed import load
from degree.models import PREMED_PROGRAM_CODE, Degree, DegreePlan, Major
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees

from .test_composition import course, leaf
from .util import set_semester


class PremedTest(TestCase):
    """A Biology BA whose major asks for general chemistry, with pre-med on top."""

    def setUp(self):
        set_semester()
        for code in ["CHEM-1011", "BIOL-2810", "CIS-1200"]:
            course(code)
        self.premed = load()
        self.biology = Degree.objects.create(program="AU_BA", degree="BA", major="BIOL", year=2026)
        self.biology.rules.add(leaf("Chemistry", "CHEM-1011", "MAJOR", "BIOL"))
        self.plan = DegreePlan.objects.create(
            name="premed", person=get_user_model().objects.create_user(username="m")
        )
        self.plan.degrees.add(self.biology)
        self.plan.majors.add(self.premed)

    def selected(self, full_code):
        plan_rules = map_rules_and_degrees(self.plan)
        selected, _, legal = allocate_rules(
            full_code,
            plan_rules.rules_per_component,
            plan_rules.rule_to_component,
            plan_rules.double_counts,
            satisfied_rules=set(),
            policy=plan_rules.composition.policy,
        )
        self.assertTrue(legal)
        return {rule.title for rule in selected}

    def test_a_premed_course_also_counts_toward_the_major(self):
        self.assertEqual(self.selected("CHEM-1011"), {"Chemistry", "CHEM 1011 or 1012"})

    def test_premed_takes_none_of_a_courses_degree_claims(self):
        computing = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        computing.rules.add(leaf("Computing Chemistry", "CHEM-1011", "MAJOR", "CIS"))
        self.plan.degrees.add(computing)
        self.assertEqual(
            self.selected("CHEM-1011"),
            {"Chemistry", "Computing Chemistry", "CHEM 1011 or 1012"},
        )

    def test_a_course_counts_once_within_premed(self):
        selected = self.selected("BIOL-2810")
        self.assertEqual(len(selected & {"Biochemistry", "2000-Level Biology Lecture"}), 1)

    def test_the_plan_shows_it_as_pre_medicine(self):
        titles = {
            component.title for component in map_rules_and_degrees(self.plan).composition.components
        }
        self.assertIn("Pre-Medicine", titles)

    def test_loading_again_keeps_one_premed_major_and_its_rules(self):
        rules = set(self.premed.rules.values_list("id", flat=True))
        load()
        self.assertEqual(Major.objects.filter(program_code=PREMED_PROGRAM_CODE).count(), 1)
        self.assertEqual(set(self.premed.rules.values_list("id", flat=True)), rules)
