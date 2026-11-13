from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import SimpleTestCase, TestCase
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
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees, matches_without_record
from degree.views import update_fulfillments
from tests.degree.util import TEST_SEMESTER, set_semester


class MatchesWithoutRecordTest(SimpleTestCase):
    def test_a_q_naming_the_code_matches(self):
        self.assertTrue(matches_without_record(Q(full_code="EAS-0091"), "EAS-0091"))
        q = Q(full_code="CHEM-1012") | Q(full_code="EAS-0091")
        self.assertTrue(matches_without_record(q, "EAS-0091"))
        self.assertTrue(matches_without_record(Q(full_code__in=["EAS-0091"]), "EAS-0091"))
        self.assertFalse(matches_without_record(q, "EAS-0092"))

    def test_a_department_and_number_range_is_judged_from_the_code(self):
        q = Q(department__code="EAS", code__gte="0000", code__lte="0999")
        self.assertTrue(matches_without_record(q, "EAS-0091"))
        self.assertFalse(matches_without_record(q, "EAS-1000"))
        self.assertFalse(matches_without_record(q, "CHEM-0091"))
        self.assertTrue(matches_without_record(Q(department__code__in=["EAS"]), "EAS-0091"))

    def test_what_only_a_record_could_say_does_not_match(self):
        self.assertFalse(matches_without_record(Q(attributes__code__in=["EUNS"]), "EAS-0091"))
        q = Q(full_code="EAS-0091", semester__lt="2020A")
        self.assertFalse(matches_without_record(q, "EAS-0091"))
        self.assertTrue(matches_without_record(~Q(full_code="CHEM-1012"), "EAS-0091"))


class UnrecordedCourseTest(TestCase):
    """
    EAS 0091 is the code Penn gives AP Chemistry credit. It is never scheduled, so there is no
    Course for it, but Engineering's Chemistry or Biology requirement names it.
    """

    def setUp(self):
        set_semester()
        get_or_create_course_and_section("CHEM-1012-001", TEST_SEMESTER)

        self.user = get_user_model().objects.create_user(username="u", password="x")
        PDPBetaUser.objects.create(person=self.user)

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="EE", year=2026)
        science = Rule.objects.create(
            title="Math and Natural Science", block_type="OTHER", block_value="U-MNS"
        )
        self.chemistry = Rule.objects.create(
            title="Chemistry or Biology Course",
            parent=science,
            q=repr(Q(full_code="CHEM-1012") | Q(full_code="EAS-0091")),
            num=1,
            block_type="OTHER",
            block_value="U-MNS",
        )
        self.degree.rules.add(science)

        self.plan = DegreePlan.objects.create(name="EE", person=self.user)
        self.plan.degrees.add(self.degree)
        Fulfillment.objects.create(
            degree_plan=self.plan, full_code="EAS-0091", semester=TRANSFER_CREDIT_SEMESTER
        )

        self.client = APIClient()
        self.client.force_login(self.user)

    def rules_of_ap_chemistry(self):
        return set(self.plan.fulfillments.get(full_code="EAS-0091").rules.all())

    def test_reallocating_the_plan_keeps_it_on_the_requirement_naming_it(self):
        update_fulfillments(self.plan)
        self.assertEqual(self.rules_of_ap_chemistry(), {self.chemistry})

    def test_it_is_allocated_on_its_own(self):
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        selected, _, _ = allocate_rules(
            "EAS-0091",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            degree_plan=self.plan,
            is_transfer=True,
        )
        self.assertEqual(selected, {self.chemistry})

    def test_it_satisfies_the_requirement(self):
        self.assertTrue(self.chemistry.evaluate(["EAS-0091"]))
        self.assertTrue(self.chemistry.check_belongs("EAS-0091"))
        self.assertFalse(self.chemistry.evaluate(["EAS-0092"]))

    def test_waiving_and_lifting_the_requirement_puts_it_back(self):
        url = reverse("degreeplan-waivers", kwargs={"pk": self.plan.id})
        update_fulfillments(self.plan)
        self.client.post(url, {"rule_ids": [self.chemistry.id]}, format="json")
        self.assertEqual(self.rules_of_ap_chemistry(), set())

        response = self.client.delete(url, {"rule_ids": [self.chemistry.id]}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.rules_of_ap_chemistry(), {self.chemistry})
