from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Q
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from degree.models import (
    Degree,
    DegreePlan,
    DegreePlanMajor,
    DegreePlanMinor,
    Fulfillment,
    Major,
    Minor,
    PDPBetaUser,
    Rule,
)


class PlanListTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="l", password="x")
        PDPBetaUser.objects.create(person=self.user, status=PDPBetaUser.Status.APPROVED)
        self.client = APIClient()
        self.client.force_login(self.user)

    def plan(self, name):
        plan = DegreePlan.objects.create(name=name, person=self.user)
        degree = Degree.objects.create(
            program="EU_BSE",
            degree="BSE",
            major="CIS",
            major_name="Computer Science",
            concentration="AI",
            concentration_name="Artificial Intelligence",
            year=2020 + DegreePlan.objects.count(),
        )
        plan.degrees.add(degree)
        major = Major.objects.create(
            program_code=f"MATH-BA-{name}", code="MATH", name="Mathematics", year=2027
        )
        DegreePlanMajor.objects.create(degree_plan=plan, major=major, degree=degree)
        minor = Minor.objects.create(
            program_code=f"STAT-MINOR-{name}", code="STAT", name="Minor in Statistics", year=2027
        )
        DegreePlanMinor.objects.create(degree_plan=plan, minor=minor, degree=degree)
        return plan

    def test_each_plan_lists_its_programs(self):
        self.plan("A")
        DegreePlan.objects.create(name="Empty", person=self.user)
        response = self.client.get(reverse("degreeplan-list"))
        programs = {plan["name"]: plan["programs"] for plan in response.json()}
        self.assertEqual(
            programs["A"],
            [
                {
                    "kind": "degree",
                    "code": "CIS",
                    "name": "BSE in Computer Science (Artificial Intelligence)",
                    "progress": 0,
                },
                {"kind": "major", "code": "MATH", "name": "Major in Mathematics", "progress": 0},
                {"kind": "minor", "code": "STAT", "name": "Minor in Statistics", "progress": 0},
            ],
        )
        self.assertEqual(programs["Empty"], [])

    def list_queries(self):
        with CaptureQueriesContext(connection) as queries:
            self.client.get(reverse("degreeplan-list"))
        return len(queries)

    def test_listing_more_plans_takes_no_more_queries(self):
        self.plan("A")
        one = self.list_queries()
        self.plan("B")
        self.plan("C")
        self.assertEqual(self.list_queries(), one)


class PlanProgressTest(TestCase):
    """
    A minor of two top-level requirements: Calculus asks for two courses, and Electives for one
    of two tracks, each asking for one course.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="p", password="x")
        PDPBetaUser.objects.create(person=self.user, status=PDPBetaUser.Status.APPROVED)
        self.client = APIClient()
        self.client.force_login(self.user)

        self.minor = Minor.objects.create(
            program_code="MATH-MINOR", code="MATH", name="Math", year=2027
        )
        self.calculus = self.leaf("Calculus", num=2)
        electives = Rule.objects.create(title="Electives", num=1)
        self.algebra = self.leaf("Algebra", num=1, parent=electives)
        self.leaf("Analysis", num=1, parent=electives)
        self.minor.rules.add(self.calculus, electives)

        self.plan = DegreePlan.objects.create(name="Math", person=self.user)
        DegreePlanMinor.objects.create(degree_plan=self.plan, minor=self.minor)

    def leaf(self, title, num, parent=None):
        return Rule.objects.create(
            title=title, q=repr(Q(department__code="MATH")), num=num, parent=parent
        )

    def place(self, full_code, rule):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code=full_code, semester="2025A"
        )
        fulfillment.rules.add(rule)

    def progress(self):
        response = self.client.get(reverse("degreeplan-list"))
        return response.json()[0]["programs"][0]["progress"]

    def test_a_requirement_counts_toward_how_many_courses_it_asks_for(self):
        self.place("MATH-1400", self.calculus)
        self.assertEqual(self.progress(), 0.25)

    def test_a_group_counts_only_as_many_children_as_it_asks_for(self):
        self.place("MATH-3700", self.algebra)
        self.assertEqual(self.progress(), 0.5)

    def test_a_waived_requirement_is_complete(self):
        self.plan.waived_rules.add(self.calculus)
        self.assertEqual(self.progress(), 0.5)
