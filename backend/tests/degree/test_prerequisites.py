from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser
from degree.serializers import prerequisite_rules_by_full_code
from tests.courses.util import fill_course_soft_state


TEST_SEMESTER = "2024C"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class PrerequisiteRulesByFullCodeTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.cis_1200, _, _, _ = get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)
        self.cis_1210, _, _, _ = get_or_create_course_and_section("CIS-1210-001", TEST_SEMESTER)
        self.old_cis_1210, _, _, _ = get_or_create_course_and_section("CIS-1210-001", "2023C")
        fill_course_soft_state()

    def test_most_recent_rule_wins(self):
        self.old_cis_1210.prerequisite_rule = "CIS-1600"
        self.old_cis_1210.save()
        self.assertEqual(prerequisite_rules_by_full_code(["CIS-1210"]), {"CIS-1210": "CIS-1600"})
        self.cis_1210.prerequisite_rule = {"or": ["CIS-1200", "CIS-1600"]}
        self.cis_1210.save()
        self.assertEqual(
            prerequisite_rules_by_full_code(["CIS-1210"]),
            {"CIS-1210": {"or": ["CIS-1200", "CIS-1600"]}},
        )

    def test_courses_without_prerequisites_are_absent(self):
        self.assertEqual(prerequisite_rules_by_full_code(["CIS-1200"]), {})


class FulfillmentPrerequisiteApiTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.user = User.objects.create_user(username="test", password="top_secret")
        PDPBetaUser.objects.create(person=self.user)
        self.client = APIClient()
        self.client.force_login(self.user)

        self.cis_1200, _, _, _ = get_or_create_course_and_section("CIS-1200-001", TEST_SEMESTER)
        self.cis_1210, _, _, _ = get_or_create_course_and_section("CIS-1210-001", TEST_SEMESTER)
        fill_course_soft_state()
        self.cis_1210.prerequisite_rule = {"or": ["CIS-1200", "CIS-1600"]}
        self.cis_1210.save()

        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2023)
        self.plan = DegreePlan.objects.create(name="Plan", person=self.user)
        self.plan.degrees.add(degree)
        self.url = reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.plan.id})

    def test_fulfillment_course_lists_prerequisites(self):
        Fulfillment.objects.create(degree_plan=self.plan, full_code="CIS-1210", semester="2025A")
        Fulfillment.objects.create(degree_plan=self.plan, full_code="CIS-1200", semester="2024C")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        by_code = {f["full_code"]: f for f in response.data}
        self.assertEqual(
            by_code["CIS-1210"]["course"]["prerequisite_rule"], {"or": ["CIS-1200", "CIS-1600"]}
        )
        self.assertIsNone(by_code["CIS-1200"]["course"]["prerequisite_rule"])
        self.assertFalse(by_code["CIS-1210"]["ignore_prereqs"])

    def test_ignore_prereqs_defaults_false_and_round_trips(self):
        response = self.client.post(
            self.url, {"full_code": "CIS-1210", "semester": "2025A"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data["ignore_prereqs"])

        # The fulfillments route upserts on POST, so this updates the row above.
        response = self.client.post(
            self.url, {"full_code": "CIS-1210", "ignore_prereqs": True}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["ignore_prereqs"])
        self.assertTrue(Fulfillment.objects.get(full_code="CIS-1210").ignore_prereqs)
        # Other fields are untouched by the partial update.
        self.assertEqual(response.data["semester"], "2025A")

        response = self.client.post(
            self.url, {"full_code": "CIS-1210", "ignore_prereqs": False}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(Fulfillment.objects.get(full_code="CIS-1210").ignore_prereqs)
