from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import User
from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser, Rule, SatisfactionStatus
from tests.courses.util import fill_course_soft_state
from tests.degree.util import TEST_SEMESTER, set_semester


class RefreshSatisfactionTest(TestCase):
    def setUp(self):
        set_semester()
        self.user = User.objects.create_user(username="test", password="top_secret")
        PDPBetaUser.objects.create(person=self.user)
        for code in ["CIS-1200-001", "WRIT-0010-001"]:
            get_or_create_course_and_section(code, TEST_SEMESTER, course_defaults={"credits": 1})
        fill_course_soft_state()

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2023)
        self.major = Rule.objects.create(title="Major")
        self.cis = Rule.objects.create(
            parent=self.major, q=repr(Q(full_code__startswith="CIS")), num=1
        )
        self.writing = Rule.objects.create(title="Writing")
        self.writ = Rule.objects.create(
            parent=self.writing, q=repr(Q(full_code="WRIT-0010")), num=1
        )
        self.degree.rules.add(self.major, self.writing)

        self.plan = DegreePlan.objects.create(name="Plan", person=self.user)
        self.plan.degrees.add(self.degree)

    def add_course(self, full_code, rule):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code=full_code, semester=TEST_SEMESTER
        )
        fulfillment.rules.add(rule)
        return fulfillment

    def statuses(self):
        return {
            status.rule_id: status.satisfied
            for status in SatisfactionStatus.objects.filter(degree_plan=self.plan)
        }

    def test_refreshing_records_every_top_level_rule(self):
        self.add_course("CIS-1200", self.cis)
        self.plan.refresh_satisfaction()
        self.assertEqual(self.statuses(), {self.major.id: True, self.writing.id: False})

    def test_adding_a_course_refreshes_rules_it_is_not_assigned_to(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.post(
            reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.plan.id}),
            {"full_code": "CIS-1200", "semester": TEST_SEMESTER, "rules": []},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.statuses(), {self.major.id: True, self.writing.id: False})

    def test_removing_a_course_refreshes_every_rule(self):
        self.add_course("CIS-1200", self.cis)
        self.plan.refresh_satisfaction()

        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.delete(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.plan.id, "full_code": "CIS-1200"},
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.statuses(), {self.major.id: False, self.writing.id: False})
