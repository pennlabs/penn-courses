from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, DegreePlanMinor, Fulfillment, Minor, PDPBetaUser, Rule
from tests.degree.util import TEST_SEMESTER, set_semester


class CatalogYearTest(TestCase):
    """
    A plan's programs each come in several catalog years. The plan is a 2026 Math BA with a
    2026 Statistics minor placed under it; both also exist in 2027.
    """

    def setUp(self):
        set_semester()
        get_or_create_course_and_section("MATH-1400-001", TEST_SEMESTER)

        self.user = get_user_model().objects.create_user(username="c", password="x")
        PDPBetaUser.objects.create(person=self.user)

        self.math = {year: self.degree(year) for year in (2026, 2027)}
        self.stats = {
            year: Minor.objects.create(
                program_code="STAT-MINOR", code="STAT", name="Statistics", year=year
            )
            for year in (2026, 2027)
        }

        self.plan = DegreePlan.objects.create(name="Math", person=self.user)
        self.plan.degrees.add(self.math[2026])
        DegreePlanMinor.objects.create(
            degree_plan=self.plan, minor=self.stats[2026], degree=self.math[2026]
        )

        self.client = APIClient()
        self.client.force_login(self.user)

    def degree(self, year):
        degree = Degree.objects.create(
            program="AU_BA", degree="BA", major="MATH", major_name="Mathematics", year=year
        )
        major = Rule.objects.create(title="Major in Mathematics", block_type="MAJOR")
        Rule.objects.create(
            title="Calculus",
            parent=major,
            q=repr(Q(full_code__in=["MATH-1400"])),
            num=1,
            block_type="MAJOR",
        )
        degree.rules.add(major)
        return degree

    def switch(self, relation, from_id, to_id):
        return self.client.post(
            reverse("degreeplan-catalog-year", kwargs={"pk": self.plan.id}),
            {"relation": relation, "from_id": from_id, "to_id": to_id},
            format="json",
        )

    def test_the_plan_lists_each_programs_catalog_years(self):
        response = self.client.get(reverse("degreeplan-detail", kwargs={"pk": self.plan.id}))
        years = response.json()["catalog_years"]
        self.assertEqual(
            years["degrees"][str(self.math[2026].id)],
            [{"id": self.math[2026].id, "year": 2026}, {"id": self.math[2027].id, "year": 2027}],
        )
        self.assertEqual(
            [entry["year"] for entry in years["minors"][str(self.stats[2026].id)]], [2026, 2027]
        )

    def test_switching_a_degree_keeps_its_minor_under_it(self):
        response = self.switch("degrees", self.math[2026].id, self.math[2027].id)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(list(self.plan.degrees.all()), [self.math[2027]])
        self.assertEqual(DegreePlanMinor.objects.get(degree_plan=self.plan).degree, self.math[2027])

    def test_switching_a_minor_keeps_its_degree(self):
        response = self.switch("minors", self.stats[2026].id, self.stats[2027].id)
        self.assertEqual(response.status_code, 200, response.content)
        placement = DegreePlanMinor.objects.get(degree_plan=self.plan)
        self.assertEqual((placement.minor, placement.degree), (self.stats[2027], self.math[2026]))

    def test_courses_are_counted_for_the_new_years_requirements(self):
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester=TEST_SEMESTER
        )
        self.switch("degrees", self.math[2026].id, self.math[2027].id)
        calculus = Rule.objects.get(title="Calculus", parent__in=self.math[2027].rules.all())
        self.assertEqual(list(fulfillment.rules.all()), [calculus])

    def test_a_waiver_moves_to_the_same_requirement(self):
        old = Rule.objects.get(title="Calculus", parent__in=self.math[2026].rules.all())
        new = Rule.objects.get(title="Calculus", parent__in=self.math[2027].rules.all())
        self.plan.waived_rules.add(old)
        self.switch("degrees", self.math[2026].id, self.math[2027].id)
        self.assertEqual(list(self.plan.waived_rules.all()), [new])

    def test_only_another_year_of_the_same_program(self):
        other = Degree.objects.create(program="AU_BA", degree="BA", major="PHYS", year=2027)
        response = self.switch("degrees", self.math[2026].id, other.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(list(self.plan.degrees.all()), [self.math[2026]])

    def test_only_a_program_on_the_plan(self):
        response = self.switch("degrees", self.math[2027].id, self.math[2026].id)
        self.assertEqual(response.status_code, 400)

    def test_no_concentration_is_the_same_program_however_a_year_records_it(self):
        recorded = Degree.objects.create(
            program="AU_BA", degree="BA", major="MATH", concentration="NCON", year=2028
        )
        self.assertIn(recorded, self.math[2026].catalog_years())
        self.assertIn(self.math[2026], recorded.catalog_years())
        ncon = Minor.objects.create(program_code="STAT-MINOR-NCON", code="STAT", year=2028)
        self.assertIn(ncon, self.stats[2026].catalog_years())
