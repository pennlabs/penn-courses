from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser, Rule
from tests.degree.util import TEST_SEMESTER, set_semester


class DegreePlanAccessTest(TestCase):
    """
    The transcript onboarding and satisfied-rule-list endpoints take a degree plan ID in the
    URL, so they must only act on a plan the requesting user owns.
    """

    def setUp(self):
        set_semester()
        get_or_create_course_and_section("MATH-1400-001", TEST_SEMESTER)

        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", password="x")
        self.other = User.objects.create_user(username="other", password="x")
        PDPBetaUser.objects.create(person=self.owner)
        PDPBetaUser.objects.create(person=self.other)

        degree = Degree.objects.create(program="AU_BA", degree="BA", major="BIOL", year=2026)
        block = Rule.objects.create(title="Major", block_type="MAJOR", block_value="BIOL")
        Rule.objects.create(
            title="Calculus",
            parent=block,
            q=repr(Q(full_code__in=["MATH-1400"])),
            num=1,
            block_type="MAJOR",
            block_value="BIOL",
        )
        degree.rules.add(block)

        self.plan = DegreePlan.objects.create(name="BIOL", person=self.owner)
        self.plan.degrees.add(degree)

    def client_for(self, user):
        client = APIClient()
        if user:
            client.force_login(user)
        return client

    def onboard(self, user):
        return self.client_for(user).post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {"courses": [{"sem": TEST_SEMESTER, "courses": ["MATH-1400"]}]},
            format="json",
        )

    def satisfied_rules(self, user):
        return self.client_for(user).get(
            reverse(
                "satisfied-rule-list",
                kwargs={"degree_plan_id": self.plan.id, "full_code": "MATH-1400", "rule_id": -1},
            )
        )

    def test_onboarding_requires_login(self):
        self.assertEqual(self.onboard(None).status_code, 403)
        self.assertFalse(Fulfillment.objects.filter(degree_plan=self.plan).exists())

    def test_onboarding_another_users_plan_is_not_found(self):
        self.assertEqual(self.onboard(self.other).status_code, 404)
        self.assertFalse(Fulfillment.objects.filter(degree_plan=self.plan).exists())

    def test_owner_can_onboard(self):
        response = self.onboard(self.owner)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(Fulfillment.objects.filter(degree_plan=self.plan).exists())

    def test_satisfied_rule_list_requires_login(self):
        self.assertEqual(self.satisfied_rules(None).status_code, 403)

    def test_satisfied_rule_list_for_another_users_plan_is_not_found(self):
        self.assertEqual(self.satisfied_rules(self.other).status_code, 404)

    def test_owner_can_get_satisfied_rule_list(self):
        response = self.satisfied_rules(self.owner)
        self.assertEqual(response.status_code, 200, response.content)
