from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, Major, PDPBetaUser, Rule
from degree.utils.degree_logic import (
    allocate_rules,
    check_legal,
    map_rules_and_degrees,
    prewarm_belongs_cache,
)
from degree.utils.double_counts import get_degree_trees, resolve_double_counts
from tests.degree.util import set_semester


TEST_SEMESTER = "2023C"

THISBLOCK = [{"kind": "THISBLOCK", "value": None}]
ANY_MAJOR = [{"kind": "MAJOR", "value": None}]


class DoubleCountingTest(TestCase):
    """
    Tests that a course dropped onto a rule also counts for the rules that rule is allowed to
    double count with. This mirrors the shape of a CIS BSE degree, where the area lists double
    count with each other and with the (mutually exclusive) elective rules.

    The area lists carry a rule-scoped ShareWith (THISBLOCK), which is how an audit says that
    a rule may share with the rest of its own block; the electives carry nothing, so they are
    exclusive of each other.
    """

    def setUp(self):
        for full_code in ["CIS-5550", "CIS-5050", "CIS-1200"]:
            get_or_create_course_and_section(f"{full_code}-001", TEST_SEMESTER)

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.major_rule = Rule.objects.create(
            title="Major in Computer Science", block_type="MAJOR", block_value="CIS"
        )
        self.degree.rules.add(self.major_rule)

        self.networking = Rule.objects.create(
            title="Area List - Networking",
            parent=self.major_rule,
            q=repr(Q(full_code__in=["CIS-5550", "CIS-5050"])),
            num=1,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=THISBLOCK,
        )
        self.databases = Rule.objects.create(
            title="Area List - Databases",
            parent=self.major_rule,
            q=repr(Q(full_code__in=["CIS-5550"])),
            num=1,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=THISBLOCK,
        )
        self.engineering = Rule.objects.create(
            title="ENGINEERING", parent=self.major_rule, block_type="MAJOR", block_value="CIS"
        )
        self.cis_elective = Rule.objects.create(
            title="CIS Elective",
            parent=self.engineering,
            q=repr(Q(full_code__startswith="CIS")),
            credits=1,
            block_type="MAJOR",
            block_value="CIS",
        )
        self.tech_elective = Rule.objects.create(
            title="Unrestricted Technical Electives",
            parent=self.engineering,
            q=repr(Q(full_code__startswith="CIS")),
            credits=6,
            block_type="MAJOR",
            block_value="CIS",
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

        # The electives only double count with the area lists, not with each other: sharing is
        # symmetric, so they inherit it from the area lists without naming anything themselves
        self.assertEqual(set(self.area_lists), double_counts[self.cis_elective])
        self.assertEqual(set(self.area_lists), double_counts[self.tech_elective])

        # Non-leaf rules are never double counted with, since a course can't fulfill them
        self.assertNotIn(self.major_rule, double_counts)
        self.assertNotIn(self.engineering, double_counts)

    def test_policy_does_not_depend_on_rule_nesting(self):
        # Pre-2026 CIS degrees group their area lists under an "AREA LISTS" rule. Share targets
        # are flattened onto the leaves when the audit is parsed, so the tree shape a leaf sits
        # in makes no difference at resolution time.
        area_lists_rule = Rule.objects.create(
            title="AREA LISTS", parent=self.major_rule, block_type="MAJOR", block_value="CIS"
        )
        for area_list in self.area_lists:
            area_list.parent = area_lists_rule
            area_list.save()

        double_counts = self.double_counts()
        for area_list in self.area_lists:
            self.assertEqual(
                {*self.area_lists, *self.electives} - {area_list}, double_counts[area_list]
            )

    def test_no_share_targets(self):
        # A rule that names nothing may not double count with anything, which is the default.
        for area_list in self.area_lists:
            area_list.share_targets = []
            area_list.save()

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


class CrossDegreeDoubleCountingTest(TestCase):
    """
    Sharing between two degrees in a plan. ShareWith targets like (MAJOR) are statements about
    other programs, so they are only meaningful across degrees.
    """

    def setUp(self):
        get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)

        self.person = get_user_model().objects.create_user(username="test", password="top_secret")
        self.degree_plan = DegreePlan.objects.create(name="Dual", person=self.person)

        self.cis_degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CIS", year=2026
        )
        self.cis_rule = Rule.objects.create(
            title="Major in Computer Science",
            q=repr(Q(full_code__startswith="CIS")),
            num=1,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=ANY_MAJOR,
        )
        self.cis_degree.rules.add(self.cis_rule)

        self.math_degree = Degree.objects.create(
            program="AU_BA", degree="BA", major="MATH", year=2026
        )
        self.math_rule = Rule.objects.create(
            title="Major in Mathematics",
            q=repr(Q(full_code__startswith="CIS")),
            num=1,
            block_type="MAJOR",
            block_value="MATH",
            share_targets=ANY_MAJOR,
        )
        self.math_degree.rules.add(self.math_rule)

        self.degree_plan.degrees.add(self.cis_degree, self.math_degree)

    def test_majors_that_permit_sharing_are_legal_together(self):
        _, rule_to_degree, double_counts = map_rules_and_degrees(self.degree_plan)
        self.assertIn(self.math_rule, double_counts[self.cis_rule])
        self.assertTrue(check_legal({self.cis_rule, self.math_rule}, rule_to_degree, double_counts))

    def test_majors_that_do_not_permit_sharing_are_illegal_together(self):
        # Sharing is not free between programs: with the (MAJOR) target removed from both,
        # neither permits the other and the pairing is caught.
        for rule in [self.cis_rule, self.math_rule]:
            rule.share_targets = []
            rule.save()

        _, rule_to_degree, double_counts = map_rules_and_degrees(self.degree_plan)
        self.assertNotIn(self.cis_rule, double_counts)
        self.assertFalse(
            check_legal({self.cis_rule, self.math_rule}, rule_to_degree, double_counts)
        )

    def test_sharing_is_symmetric(self):
        # Only one side names the other, which is enough.
        self.math_rule.share_targets = []
        self.math_rule.save()

        _, rule_to_degree, double_counts = map_rules_and_degrees(self.degree_plan)
        self.assertIn(self.math_rule, double_counts[self.cis_rule])
        self.assertIn(self.cis_rule, double_counts[self.math_rule])
        self.assertTrue(check_legal({self.cis_rule, self.math_rule}, rule_to_degree, double_counts))

    def test_a_target_naming_a_specific_major(self):
        self.cis_rule.share_targets = [{"kind": "MAJOR", "value": "MATH"}]
        self.cis_rule.save()
        self.math_rule.share_targets = []
        self.math_rule.save()

        _, _, double_counts = map_rules_and_degrees(self.degree_plan)
        self.assertIn(self.math_rule, double_counts[self.cis_rule])

        # and a target naming a major that is not in the plan matches nothing
        self.cis_rule.share_targets = [{"kind": "MAJOR", "value": "PHYS"}]
        self.cis_rule.save()

        _, _, double_counts = map_rules_and_degrees(self.degree_plan)
        self.assertNotIn(self.cis_rule, double_counts)


class ComponentPassIsolationTest(TestCase):
    """
    allocate_rules walks each component and unions the results, and every pass reaches into the
    other components to find what its chosen rule may share with. A pass must speak only for
    its own component: when two passes reach different conclusions about a third, the union
    holds a pair of that component's rules that are not allowed to share, and the course is
    flagged as illegally double counted.

    The degree here has two mutually exclusive electives, and the plan also has a major whose
    rule the same course fits. Dropping the course explicitly onto the smaller elective makes
    the two passes disagree: the degree's pass honours the explicit choice, while the major's
    pass picks the larger elective on its own.
    """

    def setUp(self):
        get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)
        matches = repr(Q(full_code__startswith="CIS"))

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.big = Rule.objects.create(
            title="Unrestricted Technical Electives",
            q=matches,
            credits=6,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=ANY_MAJOR,
        )
        self.small = Rule.objects.create(
            title="Restricted or Unrestricted Technical Electives",
            q=matches,
            credits=1,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=ANY_MAJOR,
        )
        self.degree.rules.add(self.big, self.small)

        self.major = Major.objects.create(
            program_code="MATH-BA-GEN", code="MATH", name="Mathematics", year=2026
        )
        self.math_rule = Rule.objects.create(
            title="Mathematics Electives",
            q=matches,
            credits=3,
            block_type="MAJOR",
            block_value="MATH",
            share_targets=ANY_MAJOR,
        )
        self.major.rules.add(self.math_rule)

        person = get_user_model().objects.create_user(username="t", password="top_secret")
        self.plan = DegreePlan.objects.create(name="degree plus major", person=person)
        self.plan.degrees.add(self.degree)
        self.plan.majors.add(self.major)

    def test_the_two_electives_may_not_share(self):
        _, _, double_counts = map_rules_and_degrees(self.plan)
        self.assertNotIn(self.small, double_counts.get(self.big, set()))

    def test_a_pass_contributes_only_its_own_component(self):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        selected, _, legal = allocate_rules(
            "CIS-1200",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            rule_selected=self.small,
            satisfied_rules=set(),
        )

        self.assertIn(self.small, selected)
        self.assertIn(self.math_rule, selected)
        self.assertNotIn(self.big, selected)
        self.assertTrue(legal)


class NeverIllegalTest(TestCase):
    """
    The allocator must never select a pair of rules that may not share. When a course fits a
    rule in each of two components whose blocks forbid sharing, one component gets the course
    and the other is only offered it as unselected, rather than both taking it and the
    fulfillment being flagged as illegally double counted.
    """

    def setUp(self):
        get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)
        matches = repr(Q(full_code__startswith="CIS"))

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.elective = Rule.objects.create(
            title="Technical Electives",
            q=matches,
            credits=6,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=[],
        )
        self.degree.rules.add(self.elective)

        self.major = Major.objects.create(
            program_code="MATH-BA-GEN", code="MATH", name="Mathematics", year=2026
        )
        self.math_rule = Rule.objects.create(
            title="Mathematics Electives",
            q=matches,
            credits=3,
            block_type="MAJOR",
            block_value="MATH",
            share_targets=[],
        )
        self.core = Rule.objects.create(
            title="Core",
            q=repr(Q(full_code="CIS-1200")),
            num=1,
            block_type="MAJOR",
            block_value="MATH",
            share_targets=[],
        )
        self.major.rules.add(self.math_rule, self.core)

        person = get_user_model().objects.create_user(username="t", password="top_secret")
        self.plan = DegreePlan.objects.create(name="degree plus major", person=person)
        self.plan.degrees.add(self.degree)
        self.plan.majors.add(self.major)

    def allocate(self, rule_selected=None):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        return allocate_rules(
            "CIS-1200",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            rule_selected=rule_selected,
            satisfied_rules=set(),
        )

    def test_the_components_may_not_share(self):
        _, _, double_counts = map_rules_and_degrees(self.plan)
        self.assertNotIn(self.math_rule, double_counts.get(self.elective, set()))
        self.assertNotIn(self.core, double_counts.get(self.elective, set()))

    def test_only_one_component_takes_the_course(self):
        selected, unselected, legal = self.allocate()
        self.assertTrue(legal)
        self.assertEqual({self.elective}, selected)
        self.assertEqual({self.math_rule, self.core}, unselected)

    def test_an_explicit_listing_does_not_force_an_illegal_pair(self):
        # The core rule names CIS-1200 outright, which used to select it regardless of what
        # the other component had already taken.
        selected, unselected, legal = self.allocate()
        self.assertTrue(legal)
        self.assertNotIn(self.core, selected)
        self.assertIn(self.core, unselected)

    def test_the_dropped_on_rule_wins(self):
        selected, unselected, legal = self.allocate(rule_selected=self.math_rule)
        self.assertTrue(legal)
        self.assertEqual({self.math_rule}, selected)
        self.assertEqual({self.elective, self.core}, unselected)


class NeverIllegalApiTest(NeverIllegalTest):
    """
    The write paths a student reaches by dragging also never store a pair of rules that may
    not share. Where the student's new choice conflicts with what the course already counted
    for, the new choice wins and the old one is offered as unselected.
    """

    def setUp(self):
        super().setUp()
        set_semester()
        PDPBetaUser.objects.create(person=self.plan.person)
        self.client.force_login(self.plan.person)
        self.fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester=TEST_SEMESTER
        )
        self.fulfillment.rules.add(self.elective)
        self.fulfillment.unselected_rules.add(self.math_rule, self.core)

    def fulfillments_url(self):
        return reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.plan.id})

    def test_dropping_onto_a_conflicting_rule_moves_the_course(self):
        # What the requirement panel posts: the existing rules plus the one dropped on
        response = self.client.post(
            self.fulfillments_url(),
            {"full_code": "CIS-1200", "rules": [self.elective.id, self.math_rule.id]},
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.fulfillment.refresh_from_db()
        self.assertEqual({self.math_rule}, set(self.fulfillment.rules.all()))
        self.assertEqual({self.elective, self.core}, set(self.fulfillment.unselected_rules.all()))
        self.assertTrue(self.fulfillment.legal)

    def test_posting_no_rules_clears_the_flag(self):
        self.fulfillment.legal = False
        self.fulfillment.save()
        response = self.client.post(
            self.fulfillments_url(),
            {"full_code": "CIS-1200", "rules": []},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.fulfillment.refresh_from_db()
        self.assertEqual(set(), set(self.fulfillment.rules.all()))
        self.assertTrue(self.fulfillment.legal)

    def test_switching_across_components_demotes_the_conflict(self):
        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-switch-rule",
                kwargs={"degreeplan_pk": self.plan.id, "full_code": "CIS-1200"},
            ),
            {"rule_id": self.math_rule.id},
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.fulfillment.refresh_from_db()
        self.assertEqual({self.math_rule}, set(self.fulfillment.rules.all()))
        self.assertIn(self.elective, self.fulfillment.unselected_rules.all())
        self.assertTrue(self.fulfillment.legal)

    def satisfied_rule_list(self, rule_id):
        response = self.client.get(
            reverse(
                "satisfied-rule-list",
                kwargs={
                    "degree_plan_id": self.plan.id,
                    "full_code": "CIS-1200",
                    "rule_id": rule_id,
                },
            )
        )
        self.assertEqual(response.status_code, 200, response.json())
        data = response.json()
        return (
            {rule["id"] for rule in data["selected_rules"]},
            {rule["id"] for rule in data["unselected_rules"]},
            data["legal"],
        )

    def test_the_preview_keeps_what_the_course_already_counts_for(self):
        # Dragged into a semester from the requirement panel, under its current rule
        selected, unselected, legal = self.satisfied_rule_list(self.elective.id)
        self.assertEqual({self.elective.id}, selected)
        self.assertEqual({self.math_rule.id, self.core.id}, unselected)
        self.assertTrue(legal)

        # Dragged into a semester with no rule in mind
        selected, unselected, legal = self.satisfied_rule_list(-1)
        self.assertEqual({self.elective.id}, selected)
        self.assertTrue(legal)

    def test_the_preview_lets_a_new_choice_displace_the_old(self):
        selected, unselected, legal = self.satisfied_rule_list(self.math_rule.id)
        self.assertEqual({self.math_rule.id}, selected)
        self.assertEqual({self.elective.id, self.core.id}, unselected)
        self.assertTrue(legal)
