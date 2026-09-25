from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section
from degree.models import (
    TRANSFER_CREDIT_SEMESTER,
    Degree,
    DegreePlan,
    Fulfillment,
    PDPBetaUser,
    Rule,
)
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees
from degree.utils.double_counts import ANY_BLOCK
from degree.views import update_fulfillments
from tests.degree.util import TEST_SEMESTER, set_semester


class TransferCreditTest(TestCase):
    """
    AP and transfer credit does not count toward the College's Foundations or Sectors, and a
    Fulfillment is such credit when it sits in the frontend's AP & transfer semester.

    The plan is a College BA: a Formal Reasoning foundation that takes no transfer credit, and
    a major requirement that does. Both are satisfied by MATH 1400. The foundation shares with
    everything, as the real STANDALONEBLOCK Foundations block does, so a course taken at Penn
    counts for both at once and a transfer course counts only for the major.
    """

    def setUp(self):
        set_semester()
        get_or_create_course_and_section("MATH-1400-001", TEST_SEMESTER)

        self.user = get_user_model().objects.create_user(username="t", password="x")
        PDPBetaUser.objects.create(person=self.user)

        self.degree = Degree.objects.create(program="AU_BA", degree="BA", major="BIOL", year=2026)
        foundations_block = Rule.objects.create(
            title="General Education, Foundations",
            block_type="OTHER",
            block_value="U-GE-FND",
            transfer_credit_allowed=False,
        )
        self.formal_reasoning = Rule.objects.create(
            title="Formal Reasoning and Analysis",
            parent=foundations_block,
            q=repr(Q(full_code__in=["MATH-1400"])),
            num=1,
            block_type="OTHER",
            block_value="U-GE-FND",
            share_targets=[{"kind": ANY_BLOCK, "value": None}],
            transfer_credit_allowed=False,
        )
        major_block = Rule.objects.create(
            title="Major in Biology", block_type="MAJOR", block_value="BIOL"
        )
        self.calculus = Rule.objects.create(
            title="Calculus",
            parent=major_block,
            q=repr(Q(full_code__in=["MATH-1400"])),
            num=1,
            block_type="MAJOR",
            block_value="BIOL",
        )
        self.degree.rules.add(foundations_block, major_block)

        self.plan = DegreePlan.objects.create(name="BIOL", person=self.user)
        self.plan.degrees.add(self.degree)

        self.client = APIClient()
        self.client.force_login(self.user)

    def allocate(self, is_transfer):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        return allocate_rules(
            "MATH-1400",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            satisfied_rules=set(),
            is_transfer=is_transfer,
        )

    def fulfillments_url(self):
        return reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.plan.id})

    def switch_rule_url(self, full_code):
        return reverse(
            "degreeplan-fulfillment-switch-rule",
            kwargs={"degreeplan_pk": self.plan.id, "full_code": full_code},
        )

    def test_a_course_taken_at_penn_counts_for_both(self):
        selected, unselected, legal = self.allocate(is_transfer=False)
        self.assertEqual(selected, {self.formal_reasoning, self.calculus})
        self.assertTrue(legal)

    def test_transfer_credit_is_kept_off_the_foundation_entirely(self):
        selected, unselected, legal = self.allocate(is_transfer=True)
        self.assertEqual(selected, {self.calculus})
        # not even offered as an alternative
        self.assertNotIn(self.formal_reasoning, unselected)
        self.assertTrue(legal)

    def test_onboarding_from_a_transcript(self):
        response = self.client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {"courses": [{"sem": TRANSFER_CREDIT_SEMESTER, "courses": ["MATH-1400"]}]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code="MATH-1400")
        self.assertEqual(fulfillment.semester, TRANSFER_CREDIT_SEMESTER)
        self.assertTrue(fulfillment.is_transfer_credit)
        self.assertEqual(set(fulfillment.rules.all()), {self.calculus})
        self.assertNotIn(self.formal_reasoning, fulfillment.unselected_rules.all())

    def test_reallocating_a_plan_respects_transfer_credit(self):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester=TRANSFER_CREDIT_SEMESTER
        )
        update_fulfillments(self.plan)
        self.assertEqual(set(fulfillment.rules.all()), {self.calculus})

    def test_dropping_transfer_credit_on_the_foundation_is_rejected(self):
        response = self.client.post(
            self.fulfillments_url(),
            {
                "full_code": "MATH-1400",
                "semester": TRANSFER_CREDIT_SEMESTER,
                "rules": [self.formal_reasoning.id],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("transfer credit", str(response.json()))
        self.assertFalse(Fulfillment.objects.filter(full_code="MATH-1400").exists())

    def test_an_override_still_lets_it_through(self):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester=TRANSFER_CREDIT_SEMESTER
        )
        fulfillment.overrides.add(self.formal_reasoning)

        response = self.client.post(
            self.fulfillments_url(),
            {"full_code": "MATH-1400", "rules": [self.formal_reasoning.id]},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(fulfillment.rules.all()), {self.formal_reasoning})

    def test_moving_a_course_into_the_transfer_semester_drops_the_foundation(self):
        response = self.client.post(
            self.fulfillments_url(),
            {
                "full_code": "MATH-1400",
                "semester": TEST_SEMESTER,
                "rules": [self.formal_reasoning.id, self.calculus.id],
            },
        )
        self.assertEqual(response.status_code, 201, response.content)

        # the move is a semester alone, the way the planner sends it
        response = self.client.post(
            self.fulfillments_url(),
            {"full_code": "MATH-1400", "semester": TRANSFER_CREDIT_SEMESTER},
        )
        self.assertEqual(response.status_code, 200, response.content)

        fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code="MATH-1400")
        self.assertEqual(fulfillment.semester, TRANSFER_CREDIT_SEMESTER)
        self.assertEqual(set(fulfillment.rules.all()), {self.calculus})

    def test_moving_it_between_terms_at_penn_changes_nothing(self):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester=TEST_SEMESTER
        )
        fulfillment.rules.set([self.formal_reasoning, self.calculus])

        response = self.client.post(
            self.fulfillments_url(), {"full_code": "MATH-1400", "semester": "2024A"}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(set(fulfillment.rules.all()), {self.formal_reasoning, self.calculus})

    def test_switching_transfer_credit_onto_the_foundation_is_rejected(self):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester=TRANSFER_CREDIT_SEMESTER
        )
        fulfillment.rules.set([self.calculus])
        fulfillment.unselected_rules.set([self.formal_reasoning])

        response = self.client.post(
            self.switch_rule_url("MATH-1400"),
            {"rule_id": self.formal_reasoning.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("transfer credit", str(response.json()))
        self.assertEqual(set(fulfillment.rules.all()), {self.calculus})
