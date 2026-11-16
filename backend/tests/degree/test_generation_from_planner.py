"""
Scheduling contracts ported from penn-degree-planner.

Each test names the Rust test it comes from. The cases here are the ones this
backend owns: open slots, suggestions, and packing around pins. They use small
fixture degrees, not the planner's authored SEAS/Wharton trees.

Not ported, because this backend does not have those engines:

- overlap search and paired schedule blocks (`tests/overlap`, `assert_dual_schedule`)
- degree-color stripe maps (`scheduled_courses_have_degree_stripe_mapping_*`)
- authored semester hints (`tests/scheduling/templates.rs` course-placement tests)
- dual-degree 6.5 CU / five-year policy (`dual_non_cas_undergrad_gets_six_point_five_*`)
- course pools and Wharton concentration catalogs (`tests/fulfillment/pools.rs`)
- also-offered and mutex clusters (`tests/fulfillment/course_relations.rs`)

One intentional difference is called out on the half-credit test: a 0.5 CU
course reduces a 1.0 CU rule instead of being rejected outright.
"""

from decimal import Decimal

from django.db.models import Q
from django.test import TestCase

from degree.models import Degree, Fulfillment
from degree.utils.generation import generate_schedule
from degree.utils.generation.open_rules import open_slots
from degree.utils.generation.pack import next_semester
from tests.degree.test_generation import course, leaf, plan_for, semesters, use_semester


def placements_in(result, semester):
    return [row for row in result["placements"] if row["semester"] == semester]


def future_terms():
    """Fall/spring terms after the test clock (2023C)."""
    return semesters("2024C", "2025A", "2025C", "2026A", "2026C", "2027A")


class GapSemesterTests(TestCase):
    """degree_planner/tests/scheduling/gap_semester.rs"""

    def setUp(self):
        use_semester()
        for code in ("CIS-1100", "CIS-1200", "CIS-1600", "CIS-1210"):
            course(code)
        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.rules = [
            leaf(code, Q(full_code=code), num=1)
            for code in ("CIS-1100", "CIS-1200", "CIS-1600", "CIS-1210")
        ]
        self.degree.rules.set(self.rules)
        self.plan = plan_for(self.degree, username="gap-port")

    def test_gap_semester_is_not_auto_filled(self):
        terms = future_terms()
        for row in terms:
            if row["key"] == "2025A":
                row["gap"] = True
        result = generate_schedule(self.plan, terms, allow_summer=False)
        self.assertEqual(placements_in(result, "2025A"), [])

    def test_a_placed_course_stays_in_a_gap_and_nothing_else_is_added(self):
        """Rust `frozen_pin_stays_in_gap_semester`. Pins are fulfillments, not re-emitted ghosts."""
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2025A"
        )
        fulfillment.rules.add(self.rules[1])
        terms = future_terms()
        for row in terms:
            if row["key"] == "2025A":
                row["gap"] = True
        result = generate_schedule(self.plan, terms, allow_summer=False)
        self.assertEqual(placements_in(result, "2025A"), [])
        fulfillment.refresh_from_db()
        self.assertEqual(fulfillment.semester, "2025A")

    def test_gapping_a_term_relocates_items_instead_of_dropping_them(self):
        """Rust `fixed_hint_does_not_dump_into_gap`, without authored hints."""
        baseline = generate_schedule(self.plan, future_terms(), allow_summer=False)
        gapped_terms = future_terms()
        for row in gapped_terms:
            if row["key"] == "2025A":
                row["gap"] = True
        gapped = generate_schedule(self.plan, gapped_terms, allow_summer=False)
        self.assertEqual(len(baseline["placements"]), len(gapped["placements"]))
        self.assertEqual(placements_in(gapped, "2025A"), [])

    def test_enough_gaps_extend_the_schedule(self):
        """Rust `enough_gaps_expand_past_year_four`."""
        terms = semesters("2024C", "2025A", "2025C", "2026A")
        for row in terms:
            row["gap"] = True
        result = generate_schedule(self.plan, terms, allow_summer=False)
        self.assertTrue(result["semesters"])
        self.assertTrue(result["placements"])
        self.assertTrue(all(row["semester"] > "2026A" for row in result["placements"]))


class CreditCapTests(TestCase):
    """
    degree_planner/tests/scheduling/generate.rs

    Only the caps this packer implements: 5.5 CU for a fall or spring term and
    2.0 CU for summer. Dual-degree 6.5 CU defaults are not implemented here.
    """

    def setUp(self):
        use_semester()
        codes = [f"CIS-{1100 + i}" for i in range(8)]
        for code in codes:
            course(code)
        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CIS", year=2026, concentration="CAP"
        )
        self.degree.rules.set([leaf(code, Q(full_code=code), num=1) for code in codes])
        self.plan = plan_for(self.degree, username="cap-port")

    def test_fall_and_spring_suggestions_stay_within_five_point_five(self):
        result = generate_schedule(self.plan, future_terms(), allow_summer=False)
        used = {}
        for row in result["placements"]:
            used[row["semester"]] = used.get(row["semester"], 0) + row["cu"]
        for semester, cu in used.items():
            self.assertLessEqual(cu, 5.5 + 1e-6, semester)
            self.assertFalse(semester.endswith("B"))

    def test_summer_cap_is_two_cu(self):
        terms = semesters("2024B", "2024C", cap=5.5)
        for row in terms:
            if row["key"].endswith("B"):
                row["cu_cap"] = None
        result = generate_schedule(self.plan, terms, allow_summer=True)
        summer = sum(row["cu"] for row in placements_in(result, "2024B"))
        self.assertLessEqual(summer, 2.0 + 1e-6)
        self.assertGreater(summer, 0)

    def test_no_course_is_suggested_twice(self):
        """Rust `biol_wh_nofl_finishes_in_four_years_without_duplicate_placeholders`."""
        result = generate_schedule(self.plan, future_terms(), allow_summer=False)
        codes = [row["full_code"] for row in result["placements"] if row["full_code"]]
        self.assertEqual(len(codes), len(set(codes)))
        slot_ids = [slot for row in result["placements"] for slot in row["slot_ids"]]
        self.assertEqual(len(slot_ids), len(set(slot_ids)))


class OpenSlotTests(TestCase):
    """degree_planner/tests/fulfillment/requirements.rs"""

    def setUp(self):
        use_semester()
        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CIS", year=2026, concentration="SLOT"
        )
        self.plan = plan_for(self.degree, username="slot-port")

    def test_a_four_course_restriction_emits_one_slot_per_remaining_course(self):
        for code in ("TEST-1000", "TEST-1001", "TEST-1002", "TEST-1003"):
            course(code)
        rule = leaf("Test elective", Q(department__code="TEST"), num=4)
        self.degree.rules.add(rule)
        for code in ("TEST-1000", "TEST-1001"):
            fulfillment = Fulfillment.objects.create(
                degree_plan=self.plan, full_code=code, semester="2023C"
            )
            fulfillment.rules.add(rule)
        slots = [slot for slot in open_slots(self.plan) if slot.rule_id == rule.id]
        self.assertEqual(len(slots), 2)
        self.assertTrue(all(slot.slot_id.startswith(f"slot:{rule.id}:") for slot in slots))
        self.assertTrue(all(not slot.slot_id.startswith("TEST") for slot in slots))

    def test_half_credit_reduces_a_one_credit_rule_instead_of_ignoring_the_course(self):
        """
        Rust `half_cu_course_does_not_fill_one_cu_slot` rejects the 0.5 CU course.
        This backend subtracts it and leaves a 0.5 CU slot, which is how credit
        remainders are packed.
        """
        course("TEST-1000", credits=0.5)
        rule = leaf("One CU elective", Q(full_code="TEST-1000"), credits=Decimal("1"))
        self.degree.rules.add(rule)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="TEST-1000", semester="2023C"
        )
        fulfillment.rules.add(rule)
        slots = [slot for slot in open_slots(self.plan) if slot.rule_id == rule.id]
        self.assertEqual([slot.cu for slot in slots], [Decimal("0.5")])

    def test_an_either_or_group_uses_the_requirement_title(self):
        """Rust `anyof_placeholder_uses_category_name_not_generic_options_text`."""
        course("BIOL-2000")
        parent = leaf("Additional Biology", Q(), num=1)
        parent.q = ""
        parent.save()
        child = leaf(
            "Biology 2000-level", Q(department__code="BIOL", code__gte="2000"), num=1, parent=parent
        )
        self.degree.rules.add(parent)
        slots = open_slots(self.plan)
        self.assertTrue(
            any(slot.rule_id == child.id and slot.label == "Biology 2000-level" for slot in slots)
        )
        self.assertFalse(any("following options" in slot.label.lower() for slot in slots))

    def test_a_taken_named_course_is_not_suggested_again(self):
        """Rust `taken_courses_partition_into_fulfilled_and_open`."""
        course("CIS-1100")
        course("CIS-1200")
        first = leaf("1100", Q(full_code="CIS-1100"), num=1)
        second = leaf("1200", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(first, second)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1100", semester="2023C"
        )
        fulfillment.rules.add(first)
        result = generate_schedule(self.plan, future_terms(), allow_summer=False)
        suggested = {row["full_code"] for row in result["placements"]}
        self.assertNotIn("CIS-1100", suggested)
        self.assertIn("CIS-1200", suggested)


class SemesterOrderTests(TestCase):
    """degree_planner/tests/scheduling/templates.rs semester-order helpers."""

    def test_fall_spring_order_moves_forward(self):
        self.assertEqual(next_semester("2026C", False), "2027A")
        self.assertEqual(next_semester("2027A", False), "2027C")
        self.assertLess("2026C", "2027A")
        self.assertLess(next_semester("2027A", False), next_semester("2027C", False))

    def test_summer_is_between_spring_and_fall_only_when_allowed(self):
        self.assertEqual(next_semester("2027A", True), "2027B")
        self.assertEqual(next_semester("2027B", True), "2027C")
        self.assertEqual(next_semester("2027A", False), "2027C")
