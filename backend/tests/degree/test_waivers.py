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
    SatisfactionStatus,
)
from degree.utils.double_counts import ANY_BLOCK
from degree.views import update_fulfillments
from tests.degree.util import TEST_SEMESTER, set_semester


class WaiverTest(TestCase):
    """
    A waiver satisfies a requirement without a course and without course units, as a 5 on AP
    Microeconomics and Macroeconomics does Wharton's Introductory Economics.

    The plan is a Wharton BS whose First-Year Foundations hold Introductory Economics (BEPP
    1000) and a writing seminar, alongside a business breadth elective that BEPP 1000 can also
    count toward.
    """

    def setUp(self):
        set_semester()
        for code in ["BEPP-1000-001", "WRIT-0370-001", "MGMT-1010-001"]:
            get_or_create_course_and_section(code, TEST_SEMESTER)

        self.user = get_user_model().objects.create_user(username="w", password="x")
        PDPBetaUser.objects.create(person=self.user)

        self.degree = Degree.objects.create(program="WU_BS", degree="BS", major="FNCE", year=2026)
        self.foundations = Rule.objects.create(
            title="First-Year Foundations", block_type="OTHER", block_value="U-WFYF"
        )
        self.intro_econ = self.leaf("Introductory Economics", ["BEPP-1000"], self.foundations)
        self.writing = self.leaf("Critical Writing Seminar", ["WRIT-0370"], self.foundations)
        breadth = Rule.objects.create(
            title="Business Breadth", block_type="OTHER", block_value="U-WBBR"
        )
        self.breadth_elective = Rule.objects.create(
            title="Business Breadth",
            parent=breadth,
            q=repr(Q(department__code__in=["BEPP", "MGMT"])),
            num=1,
            block_type="OTHER",
            block_value="U-WBBR",
        )
        self.degree.rules.add(self.foundations, breadth)

        self.plan = DegreePlan.objects.create(name="Wharton", person=self.user)
        self.plan.degrees.add(self.degree)

        self.client = APIClient()
        self.client.force_login(self.user)

    def leaf(self, title, full_codes, parent):
        return Rule.objects.create(
            title=title,
            parent=parent,
            q=repr(Q(full_code__in=full_codes)),
            num=1,
            block_type=parent.block_type,
            block_value=parent.block_value,
        )

    def waive(self, *rules, method="post"):
        return getattr(self.client, method)(
            reverse("degreeplan-waivers", kwargs={"pk": self.plan.id}),
            {"rule_ids": [rule.id for rule in rules]},
            format="json",
        )

    def add_course(self, full_code, semester=TEST_SEMESTER):
        Fulfillment.objects.create(degree_plan=self.plan, full_code=full_code, semester=semester)
        update_fulfillments(self.plan)

    def rules_of(self, full_code):
        return set(Fulfillment.objects.get(degree_plan=self.plan, full_code=full_code).rules.all())

    def foundations_satisfied(self):
        return SatisfactionStatus.objects.get(
            degree_plan=self.plan, rule=self.foundations
        ).satisfied

    def test_a_waived_requirement_is_satisfied_without_a_course(self):
        self.add_course("WRIT-0370")
        self.assertFalse(self.foundations_satisfied())

        response = self.waive(self.intro_econ)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["waived_rules"], [self.intro_econ.id])
        self.assertTrue(self.foundations_satisfied())
        # nothing was added to the plan to satisfy it, so it carries no course units
        self.assertEqual(
            list(self.plan.fulfillments.values_list("full_code", flat=True)), ["WRIT-0370"]
        )

    def test_a_waived_requirement_takes_none_of_the_plans_courses(self):
        self.add_course("BEPP-1000")
        self.assertIn(self.intro_econ, self.rules_of("BEPP-1000"))

        self.waive(self.intro_econ)
        self.assertEqual(self.rules_of("BEPP-1000"), {self.breadth_elective})

    def test_a_course_that_could_share_is_not_moved_onto_a_waived_requirement(self):
        # With sharing allowed, rebalancing would otherwise fill the empty requirement.
        self.breadth_elective.share_targets = [{"kind": ANY_BLOCK, "value": None}]
        self.breadth_elective.save()
        self.waive(self.intro_econ)

        self.add_course("BEPP-1000")
        self.assertEqual(self.rules_of("BEPP-1000"), {self.breadth_elective})

    def test_lifting_a_waiver_restores_the_requirement(self):
        self.add_course("WRIT-0370")
        self.waive(self.intro_econ)

        response = self.waive(self.intro_econ, method="delete")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["waived_rules"], [])
        self.assertFalse(self.foundations_satisfied())

    def test_waiving_a_block_waives_every_requirement_in_it(self):
        self.add_course("BEPP-1000")
        self.waive(self.foundations)

        self.assertTrue(self.foundations_satisfied())
        self.assertEqual(
            self.plan.check_rules_already_satisfied({self.intro_econ, self.writing}),
            {self.intro_econ, self.writing},
        )
        self.assertEqual(self.rules_of("BEPP-1000"), {self.breadth_elective})

    def test_onboarding_skips_waived_requirements(self):
        self.waive(self.intro_econ)
        response = self.client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {"courses": [{"sem": TRANSFER_CREDIT_SEMESTER, "courses": ["BEPP-1000"]}]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.rules_of("BEPP-1000"), {self.breadth_elective})

    def test_copying_a_plan_keeps_its_waivers(self):
        self.waive(self.intro_econ)
        copy = self.plan.copy("Wharton copy")
        self.assertEqual(list(copy.waived_rules.all()), [self.intro_econ])

    def test_only_the_plans_own_requirements_can_be_waived(self):
        other = Rule.objects.create(
            title="Not in this plan", q=repr(Q(full_code="MGMT-1010")), num=1
        )
        response = self.waive(other)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.plan.waived_rules.exists())

        response = self.client.post(
            reverse("degreeplan-waivers", kwargs={"pk": self.plan.id}),
            {"rule_ids": self.intro_econ.id},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_evaluating_a_rule_counts_waived_children(self):
        self.assertFalse(self.foundations.evaluate(["WRIT-0370"]))
        self.assertTrue(self.foundations.evaluate(["WRIT-0370"], waived={self.intro_econ.id}))
        self.assertTrue(self.intro_econ.evaluate([], waived={self.intro_econ.id}))
