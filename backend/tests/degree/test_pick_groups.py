from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser, Rule
from degree.utils.degree_logic import PickGroups, allocate_rules, map_rules_and_degrees
from degree.views import update_fulfillments
from tests.degree.util import TEST_SEMESTER, set_semester


class PickGroupTest(TestCase):
    """
    Biology's introductory requirement is one of two tracks: BIOL 1121 with its lab, or BIOL
    1101. Any BIOL course also counts as a Biology elective, in a block of its own.
    """

    def setUp(self):
        set_semester()
        for code in ["BIOL-1101", "BIOL-1121", "BIOL-1123"]:
            get_or_create_course_and_section(f"{code}-001", TEST_SEMESTER)

        self.user = get_user_model().objects.create_user(username="p", password="x")
        PDPBetaUser.objects.create(person=self.user)

        self.degree = Degree.objects.create(program="AU_BA", degree="BA", major="BIOL", year=2026)
        major = Rule.objects.create(
            title="Major in Biology", block_type="MAJOR", block_value="BIOL"
        )
        self.introductory = self.group("Introductory Biology", major, num=1)
        track_one = self.group("Track One", self.introductory)
        self.lecture = self.leaf("Lecture", Q(full_code="BIOL-1121"), track_one)
        self.lab = self.leaf("Lab", Q(full_code="BIOL-1123"), track_one)
        self.track_two = self.leaf("Track Two", Q(full_code="BIOL-1101"), self.introductory)
        electives = Rule.objects.create(
            title="Electives", block_type="OTHER", block_value="BIOL-ELECTIVES"
        )
        self.elective = Rule.objects.create(
            title="Biology Elective",
            parent=electives,
            q=repr(Q(department__code="BIOL")),
            credits=3,
            block_type="OTHER",
            block_value="BIOL-ELECTIVES",
        )
        self.degree.rules.add(major, electives)

        self.plan = DegreePlan.objects.create(name="Biology", person=self.user)
        self.plan.degrees.add(self.degree)

        self.client = APIClient()
        self.client.force_login(self.user)

    def group(self, title, parent, num=None):
        return Rule.objects.create(
            title=title, parent=parent, num=num, block_type="MAJOR", block_value="BIOL"
        )

    def leaf(self, title, q, parent):
        return Rule.objects.create(
            title=title, parent=parent, q=repr(q), num=1, block_type="MAJOR", block_value="BIOL"
        )

    def take(self, full_code, semester):
        Fulfillment.objects.create(degree_plan=self.plan, full_code=full_code, semester=semester)

    def rules_of(self, full_code):
        return set(self.plan.fulfillments.get(full_code=full_code).rules.all())

    def unselected_of(self, full_code):
        return set(self.plan.fulfillments.get(full_code=full_code).unselected_rules.all())

    def test_a_finished_track_closes_the_other(self):
        leaves = {self.lecture, self.lab, self.track_two, self.elective}
        self.assertEqual(PickGroups(leaves).closed({self.track_two}), {self.lecture, self.lab})
        self.assertEqual(PickGroups(leaves).closed({self.lecture, self.lab}), {self.track_two})

    def test_part_of_a_track_closes_nothing(self):
        leaves = {self.lecture, self.lab, self.track_two, self.elective}
        self.assertEqual(PickGroups(leaves).closed({self.lecture}), set())

    def test_reallocating_leaves_the_other_track_for_the_student_to_choose(self):
        self.take("BIOL-1101", "2024A")
        self.take("BIOL-1121", "2024C")
        update_fulfillments(self.plan)

        self.assertEqual(self.rules_of("BIOL-1101"), {self.track_two})
        self.assertEqual(self.rules_of("BIOL-1121"), {self.elective})
        self.assertIn(self.lecture, self.unselected_of("BIOL-1121"))

    def test_the_transcript_loader_leaves_the_other_track_too(self):
        response = self.client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {
                "courses": [
                    {"sem": "2024A", "courses": ["BIOL-1101"]},
                    {"sem": "2024C", "courses": ["BIOL-1121"]},
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.rules_of("BIOL-1121"), {self.elective})

    def test_adding_a_course_leaves_the_other_track_too(self):
        self.take("BIOL-1101", "2024A")
        update_fulfillments(self.plan)

        plan_rules = map_rules_and_degrees(self.plan)
        selected, unselected, _ = allocate_rules(
            "BIOL-1121",
            plan_rules.rules_per_component,
            plan_rules.rule_to_component,
            plan_rules.double_counts,
            degree_plan=self.plan,
        )
        self.assertEqual(selected, {self.elective})
        self.assertIn(self.lecture, unselected)

    def test_a_track_half_done_still_takes_its_other_course(self):
        self.take("BIOL-1121", "2024A")
        self.take("BIOL-1123", "2024C")
        update_fulfillments(self.plan)

        self.assertEqual(self.rules_of("BIOL-1121"), {self.lecture})
        self.assertEqual(self.rules_of("BIOL-1123"), {self.lab})
