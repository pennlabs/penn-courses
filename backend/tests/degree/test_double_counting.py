from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Rule
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees, prewarm_belongs_cache
from degree.utils.double_counts import get_degree_trees, resolve_double_counts


TEST_SEMESTER = "2023C"


class DoubleCountingTest(TestCase):
    """
    Tests that a course dropped onto a rule also counts for the rules that rule is allowed to
    double count with. This mirrors the shape of a CIS BSE degree, where the area lists double
    count with each other and with the (mutually exclusive) elective rules.
    """

    def setUp(self):
        for full_code in ["CIS-5550", "CIS-5050", "CIS-1200"]:
            get_or_create_course_and_section(f"{full_code}-001", TEST_SEMESTER)

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.major_rule = Rule.objects.create(title="Major in Computer Science")
        self.degree.rules.add(self.major_rule)

        # Newer CIS degrees have their area lists as leaf rules of the major rule
        self.networking = Rule.objects.create(
            title="Area List - Networking",
            parent=self.major_rule,
            q=repr(Q(full_code__in=["CIS-5550", "CIS-5050"])),
            num=1,
        )
        self.databases = Rule.objects.create(
            title="Area List - Databases",
            parent=self.major_rule,
            q=repr(Q(full_code__in=["CIS-5550"])),
            num=1,
        )
        self.engineering = Rule.objects.create(title="ENGINEERING", parent=self.major_rule)
        self.cis_elective = Rule.objects.create(
            title="CIS Elective",
            parent=self.engineering,
            q=repr(Q(full_code__startswith="CIS")),
            credits=1,
        )
        self.tech_elective = Rule.objects.create(
            title="Unrestricted Technical Electives",
            parent=self.engineering,
            q=repr(Q(full_code__startswith="CIS")),
            credits=6,
        )
        self.area_lists = [self.networking, self.databases]
        self.electives = [self.cis_elective, self.tech_elective]

        self.degree_plan = DegreePlan.objects.create(
            name="Test Degree Plan",
            person=get_user_model().objects.create_user(username="test", password="top_secret"),
        )
        self.degree_plan.degrees.add(self.degree)

    def double_counts(self):
        return resolve_double_counts(get_degree_trees([self.degree]))

    def allocate(self, full_code, rule_selected=None):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.degree_plan)
        return allocate_rules(
            full_code,
            rules_per_degree,
            rule_to_degree,
            double_counts,
            rule_selected,
            satisfied_rules=set(),
        )

    def test_resolve_double_counts(self):
        double_counts = self.double_counts()

        # An area list double counts with the other area lists and every elective, but not
        # with itself
        for area_list in self.area_lists:
            self.assertEqual(
                {*self.area_lists, *self.electives} - {area_list}, double_counts[area_list]
            )

        # The electives only double count with the area lists, not with each other
        self.assertEqual(set(self.area_lists), double_counts[self.cis_elective])
        self.assertEqual(set(self.area_lists), double_counts[self.tech_elective])

        # Non-leaf rules are never double counted with, since a course can't fulfill them
        self.assertNotIn(self.major_rule, double_counts)
        self.assertNotIn(self.engineering, double_counts)

    def test_resolve_double_counts_for_parent_rule(self):
        # Pre-2026 CIS degrees use the CSCI major code and group their area lists under an
        # "AREA LISTS" rule, so the policy has to resolve through a parent rule
        self.degree.major = "CSCI"
        self.degree.save()
        area_lists_rule = Rule.objects.create(title="AREA LISTS", parent=self.major_rule)
        for area_list in self.area_lists:
            area_list.parent = area_lists_rule
            area_list.save()

        double_counts = self.double_counts()
        for area_list in self.area_lists:
            self.assertEqual(
                {*self.area_lists, *self.electives} - {area_list}, double_counts[area_list]
            )

    def test_no_policy_for_degree(self):
        self.degree.major = "MEAM"
        self.degree.save()

        selected, unselected, legal = self.allocate("CIS-5550", self.networking)
        self.assertEqual({self.networking}, selected)
        self.assertEqual({self.databases, *self.electives}, unselected)
        self.assertTrue(legal)

    def test_double_counts_across_area_lists(self):
        selected, unselected, legal = self.allocate("CIS-5550", self.networking)

        # Both area lists double count with each other, and exactly one of the (mutually
        # exclusive) electives is picked
        self.assertIn(self.networking, selected)
        self.assertIn(self.databases, selected)
        self.assertEqual(1, len(selected & set(self.electives)))
        self.assertEqual(set(self.electives) - selected, unselected)
        self.assertTrue(legal)

    def test_double_counts_without_a_chosen_rule(self):
        selected, _, legal = self.allocate("CIS-5050")

        # CIS-5050 is only in the networking area list, so the databases rule isn't selected
        self.assertIn(self.networking, selected)
        self.assertNotIn(self.databases, selected)
        self.assertEqual(1, len(selected & set(self.electives)))
        self.assertTrue(legal)

    def test_course_outside_area_lists(self):
        selected, unselected, legal = self.allocate("CIS-1200", self.cis_elective)

        # CIS-1200 isn't in any area list, so only one elective is selected
        self.assertEqual({self.cis_elective}, selected)
        self.assertEqual({self.tech_elective}, unselected)
        self.assertTrue(legal)

    def test_prewarmed_belongs_cache(self):
        """
        Allocating with a prewarmed belongs cache (one query per rule) gives the same result as
        allocating course by course.
        """
        full_codes = ["CIS-5550", "CIS-5050", "CIS-1200"]
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.degree_plan)
        belongs_cache = prewarm_belongs_cache(
            {rule for rules in rules_per_degree.values() for rule in rules}, full_codes
        )

        for full_code in full_codes:
            self.assertEqual(
                self.allocate(full_code),
                allocate_rules(
                    full_code,
                    rules_per_degree,
                    rule_to_degree,
                    double_counts,
                    satisfied_rules=set(),
                    belongs_cache=belongs_cache,
                ),
            )
