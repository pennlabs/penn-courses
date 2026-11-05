from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import Attribute
from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser, Rule
from degree.views import update_fulfillments


SEMESTER = "2024A"
THIS_BLOCK = {"kind": "THISBLOCK", "value": None}


class AllocationBase(TestCase):
    def course(self, full_code, *attributes):
        course, _, _, _ = get_or_create_course_and_section(
            f"{full_code}-001", SEMESTER, course_defaults={"credits": 1}
        )
        for code in attributes:
            attribute, _ = Attribute.objects.get_or_create(
                code=code, defaults={"school": "SAS", "description": code}
            )
            attribute.courses.add(course)
        return course

    def rule(self, title, attribute, block, credits=None, num=None, share_targets=()):
        rule = Rule.objects.create(
            title=title,
            q=repr(Q(attributes__code__in=[attribute])),
            credits=credits,
            num=num,
            block_type="OTHER",
            block_value=block,
            share_targets=list(share_targets),
        )
        self.degree.rules.add(rule)
        return rule

    def setUp(self):
        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CSCI", concentration="X", year=2025
        )
        self.person = get_user_model().objects.create_user(username="t", password="x")
        self.plan = DegreePlan.objects.create(name="plan", person=self.person)
        self.plan.degrees.add(self.degree)

    def add(self, *full_codes):
        for index, full_code in enumerate(full_codes):
            Fulfillment.objects.create(
                degree_plan=self.plan, full_code=full_code, semester=f"{2020 + index}A"
            )

    def fills(self, rule):
        return set(
            Fulfillment.objects.filter(degree_plan=self.plan, rules=rule).values_list(
                "full_code", flat=True
            )
        )


class OverfillTest(AllocationBase):
    def test_a_shared_rule_stops_at_its_requirement(self):
        tech = self.rule("Tech", "TECH", "A", credits=2, share_targets=[{"kind": "OTHER"}])
        self.rule("Area", "AREA", "B", credits=3, share_targets=[{"kind": "OTHER"}])
        for code in ["CIS-5000", "CIS-5010", "CIS-5020"]:
            self.course(code, "TECH", "AREA")

        self.add("CIS-5000", "CIS-5010", "CIS-5020")
        update_fulfillments(self.plan)

        self.assertEqual(self.fills(tech), {"CIS-5000", "CIS-5010"})

    def test_a_course_past_the_limit_is_still_offered(self):
        tech = self.rule("Tech", "TECH", "A", credits=1, share_targets=[{"kind": "OTHER"}])
        area = self.rule("Area", "AREA", "B", credits=3, share_targets=[{"kind": "OTHER"}])
        for code in ["CIS-5000", "CIS-5010"]:
            self.course(code, "TECH", "AREA")

        self.add("CIS-5000", "CIS-5010")
        update_fulfillments(self.plan)

        later = Fulfillment.objects.get(degree_plan=self.plan, full_code="CIS-5010")
        self.assertIn(area, later.rules.all())
        self.assertIn(tech, later.unselected_rules.all())


class RebalanceTest(AllocationBase):
    def setUp(self):
        super().setUp()
        self.tech = self.rule("Tech", "TECH", "A", credits=2)
        self.hss = self.rule("HSS", "HSS", "B", credits=1)
        self.course("BEPP-2500", "TECH", "HSS")
        self.course("CIS-5000", "TECH")
        self.course("CIS-5010", "TECH")

    def test_a_course_moves_to_the_rule_only_it_can_fill(self):
        self.add("BEPP-2500", "CIS-5000", "CIS-5010")
        update_fulfillments(self.plan)

        self.assertEqual(self.fills(self.hss), {"BEPP-2500"})
        self.assertEqual(self.fills(self.tech), {"CIS-5000", "CIS-5010"})
        moved = Fulfillment.objects.get(degree_plan=self.plan, full_code="BEPP-2500")
        self.assertIn(self.tech, moved.unselected_rules.all())
        self.assertTrue(moved.legal)

    def test_a_course_stays_put_if_nothing_can_replace_it(self):
        self.add("BEPP-2500", "CIS-5000")
        update_fulfillments(self.plan)

        # Moving BEPP 2500 would only trade one short rule for another.
        self.assertEqual(self.fills(self.tech), {"BEPP-2500", "CIS-5000"})
        self.assertEqual(self.fills(self.hss), set())

    def test_a_replacement_keeps_what_it_already_counts_for(self):
        major = self.rule("Major", "MAJOR", "C", credits=2, share_targets=[{"kind": "OTHER"}])
        self.course("CIS-5020", "MAJOR", "TECH")
        self.course("CIS-5030", "MAJOR")
        self.add("BEPP-2500", "CIS-5000", "CIS-5030", "CIS-5020")
        update_fulfillments(self.plan)

        self.assertEqual(self.fills(self.hss), {"BEPP-2500"})
        self.assertIn("CIS-5020", self.fills(self.tech))
        self.assertIn("CIS-5020", self.fills(major))

    def test_rebalancing_never_breaks_the_sharing_policy(self):
        self.add("BEPP-2500", "CIS-5000", "CIS-5010")
        update_fulfillments(self.plan)

        for fulfillment in Fulfillment.objects.filter(degree_plan=self.plan):
            self.assertTrue(fulfillment.legal, fulfillment.full_code)
            self.assertFalse({self.tech, self.hss} <= set(fulfillment.rules.all()))

    def test_onboarding_from_a_transcript_rebalances_too(self):
        PDPBetaUser.objects.create(person=self.person)
        client = APIClient()
        client.force_login(self.person)
        response = client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {"courses": [{"sem": SEMESTER, "courses": ["BEPP-2500", "CIS-5000", "CIS-5010"]}]},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.fills(self.hss), {"BEPP-2500"})
        self.assertEqual(self.fills(self.tech), {"CIS-5000", "CIS-5010"})


def fail_on_second_call():
    calls = iter([True])

    def check_legal(*args):
        try:
            return next(calls)
        except StopIteration:
            raise RuntimeError("write failed")

    return patch("degree.views.check_legal", side_effect=check_legal)


class PartialWriteTest(AllocationBase):
    def setUp(self):
        super().setUp()
        self.tech = self.rule("Tech", "TECH", "A", credits=2)
        self.course("CIS-5000", "TECH")
        self.course("CIS-5010", "TECH")
        PDPBetaUser.objects.create(person=self.person)
        self.client = APIClient()
        self.client.force_login(self.person)

    def test_a_failed_reallocation_saves_nothing(self):
        self.add("CIS-5000", "CIS-5010")
        with fail_on_second_call(), self.assertRaises(RuntimeError):
            update_fulfillments(self.plan)

        self.assertEqual(self.fills(self.tech), set())

    def test_a_failed_onboarding_saves_nothing(self):
        with fail_on_second_call(), self.assertRaises(RuntimeError):
            self.client.post(
                reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
                {"courses": [{"sem": SEMESTER, "courses": ["CIS-5000", "CIS-5010"]}]},
                format="json",
            )

        self.assertFalse(Fulfillment.objects.filter(degree_plan=self.plan).exists())

    def test_a_failed_reallocation_does_not_add_the_degree(self):
        other = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CSCI", concentration="Y", year=2025
        )
        with patch("degree.views.update_fulfillments", side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("degreeplan-degrees", kwargs={"pk": self.plan.id}),
                    {"degree_ids": [other.id]},
                    format="json",
                )

        self.assertEqual(list(self.plan.degrees.all()), [self.degree])


class MissingComponentTest(TransactionTestCase):
    def test_a_missing_degree_is_a_bad_request_and_changes_nothing(self):
        person = get_user_model().objects.create_user(username="t", password="x")
        PDPBetaUser.objects.create(person=person)
        plan = DegreePlan.objects.create(name="plan", person=person)
        client = APIClient()
        client.force_login(person)

        response = client.post(
            reverse("degreeplan-degrees", kwargs={"pk": plan.id}),
            {"degree_ids": [999999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(plan.degrees.count(), 0)
