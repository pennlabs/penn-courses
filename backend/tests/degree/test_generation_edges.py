"""
Edge cases for schedule generation.

These sit beside the happy-path tests. Each one pins a boundary: caps that
fill exactly, gaps, pins, summer, synthetic overflow, ranking ties, and
rules that are only partly done.
"""

from decimal import Decimal

from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from courses.models import Attribute
from degree.models import Degree, Fulfillment, Rule
from degree.utils.generation import generate_schedule
from degree.utils.generation.open_rules import filter_panel_options, open_slots, schedule_code
from degree.utils.model_utils import json_parser
from degree.utils.generation.pack import PackError, next_semester, pack
from degree.utils.generation.suggest import suggest

from tests.degree.test_generation import (
    TEST_SEMESTER,
    course,
    leaf,
    plan_for,
    semesters,
    use_semester,
)


def item(kind="course", cu=1.0, code="CIS-1200", slot="slot:1:0", number=1200):
    return {
        "slot_ids": [] if kind == "placement" else [slot],
        "kind": kind,
        "full_code": code,
        "fulfillment_id": 1 if kind == "placement" else None,
        "label": code or "Elective",
        "cu": cu,
        "rules": [1],
        "alternatives": [],
        "course_number": number,
    }


def by_semester(result):
    grouped = {}
    for row in result["placements"]:
        grouped.setdefault(row["semester"], []).append(row)
    return grouped


def group(title, num=None):
    return Rule.objects.create(title=title, q="", num=num)


class PackEdgeTests(TestCase):
    def setUp(self):
        use_semester()

    def test_senior_design_waits_for_senior_fall_instead_of_the_first_open_term(self):
        design = item(code="ESE-4500", slot="slot:design:0", number=4500)
        early = item(code="CIS-1200", slot="slot:1:0", number=1200)
        result = pack({"items": [design, early]}, semesters("2024C", "2025A"), pins=[])
        used = by_semester(result)
        self.assertEqual(used["2024C"][0]["full_code"], "CIS-1200")
        self.assertEqual(
            next(row for row in result["placements"] if row["full_code"] == "ESE-4500")["semester"],
            "2027C",
        )

    def test_senior_design_spring_lands_in_senior_spring(self):
        design = item(code="ESE-4510", slot="slot:design:1", number=4510)
        result = pack({"items": [design]}, semesters("2024C"), pins=[])
        self.assertEqual(result["placements"][0]["semester"], "2028A")

    def test_a_named_senior_design_stub_uses_the_same_hint(self):
        design = item(code=None, slot="slot:design:0", number=10**9)
        design["full_code"] = None
        design["short_label"] = "ESE 4500"
        design["kind"] = "placeholder"
        result = pack({"items": [design]}, semesters("2024C", "2025A"), pins=[])
        self.assertEqual(result["placements"][0]["semester"], "2027C")

    def test_a_pinned_senior_design_stays_where_the_student_put_it(self):
        design = item(code="ESE-4500", slot="slot:design:0", number=4500)
        result = pack(
            {"items": [design]},
            semesters("2024C", "2025A"),
            pins=[],
            pinned_slots=[{"slot_id": "slot:design:0", "semester": "2024C"}],
        )
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_semesters_are_filled_in_chronological_order_when_listed_backwards(self):
        result = pack({"items": [item()]}, semesters("2025A", "2024C"), pins=[])
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_a_one_cu_course_does_not_take_a_half_cu_remainder(self):
        courses = [item(code=f"CIS-{i}", slot=f"slot:1:{i}", number=i) for i in range(6)]
        result = pack({"items": courses}, semesters("2024C", "2025A"), pins=[])
        used = by_semester(result)
        self.assertEqual(len(used["2024C"]), 5)
        self.assertEqual(len(used["2025A"]), 1)
        self.assertAlmostEqual(sum(row["cu"] for row in used["2024C"]), 5.0)

    def test_a_half_credit_course_fills_the_remainder_a_whole_course_cannot(self):
        rows = [
            item(code="CIS-1000", slot="slot:1:0", number=1000, cu=1),
            item(code="CIS-1001", slot="slot:1:1", number=1001, cu=0.5),
            item(code="CIS-1002", slot="slot:1:2", number=1002, cu=1),
        ]
        result = pack({"items": rows}, semesters("2024C", "2025A", cap=1.5), pins=[])
        used = by_semester(result)
        self.assertEqual(
            [row["full_code"] for row in used["2024C"]],
            ["CIS-1000", "CIS-1001"],
        )
        self.assertEqual(used["2025A"][0]["full_code"], "CIS-1002")

    def test_a_one_cu_cap_seats_one_course_per_term(self):
        rows = [item(code=f"CIS-{i}", slot=f"slot:1:{i}", number=i) for i in range(3)]
        result = pack(
            {"items": rows},
            semesters("2024C", "2025A", "2025C", cap=1),
            pins=[],
        )
        self.assertEqual(
            [row["semester"] for row in result["placements"]],
            ["2024C", "2025A", "2025C"],
        )

    def test_a_course_too_big_for_the_column_but_under_the_default_extends(self):
        result = pack(
            {"items": [item(cu=1)]},
            [{"key": "2024C", "cu_cap": 0.5, "gap": False}],
            pins=[],
        )
        self.assertEqual(result["unplaced"], [])
        self.assertEqual(result["placements"][0]["semester"], "2025A")
        self.assertTrue(result["semesters"][0]["synthetic"])

    def test_a_course_over_the_default_cap_is_left_unplaced(self):
        result = pack(
            {"items": [item(cu=6)]},
            semesters("2024C"),
            pins=[],
        )
        self.assertEqual(result["placements"], [])
        self.assertEqual(result["semesters"], [])
        self.assertEqual(result["unplaced"][0]["reason"], "no_capacity")
        self.assertEqual(result["generated_cu"], 0)

    def test_a_pinned_slot_stays_in_a_gap(self):
        result = pack(
            {"items": [item(kind="placeholder", code=None, slot="slot:9:0", number=10**9)]},
            semesters("2024C", "2025A", gap=("2024C",)),
            pinned_slots=[{"slot_id": "slot:9:0", "semester": "2024C"}],
            pins=[],
        )
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_a_pin_to_an_unknown_semester_falls_through_to_the_next_open_term(self):
        result = pack(
            {"items": [item(slot="slot:3:0")]},
            semesters("2024C"),
            pinned_slots=[{"slot_id": "slot:3:0", "semester": "2099C"}],
            pins=[],
        )
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_two_pinned_slots_share_a_semester_even_when_that_exceeds_the_cap(self):
        rows = [
            item(kind="placeholder", code=None, slot="slot:1:0", number=1),
            item(kind="placeholder", code=None, slot="slot:1:1", number=2),
            item(code="CIS-3000", slot="slot:2:0", number=3000),
        ]
        result = pack(
            {"items": rows},
            semesters("2024C", "2025A", cap=1),
            pinned_slots=[
                {"slot_id": "slot:1:0", "semester": "2025A"},
                {"slot_id": "slot:1:1", "semester": "2025A"},
            ],
            pins=[],
        )
        pinned = [row for row in result["placements"] if row["kind"] == "placeholder"]
        self.assertEqual({row["semester"] for row in pinned}, {"2025A"})
        course_row = next(row for row in result["placements"] if row["full_code"] == "CIS-3000")
        self.assertEqual(course_row["semester"], "2024C")

    def test_an_existing_load_leaves_only_the_remainder(self):
        result = pack(
            {"items": [item(cu=1)]},
            semesters("2024C", "2025A"),
            pins=[{"semester": "2024C", "cu": 5.0, "full_code": "CIS-9999"}],
        )
        self.assertEqual(result["placements"][0]["semester"], "2025A")

    def test_an_empty_suggestion_list_places_nothing(self):
        result = pack({"items": []}, semesters("2024C", "2025A"), pins=[])
        self.assertEqual(result["placements"], [])
        self.assertEqual(result["unplaced"], [])
        self.assertEqual(result["generated_cu"], 0)

    def test_keys_that_are_not_terms_are_ignored(self):
        with self.assertRaises(PackError):
            pack({"items": []}, [{"key": "_TRAN", "cu_cap": 5.5, "gap": False}], pins=[])
        result = pack(
            {"items": [item()]},
            [{"key": "", "cu_cap": 5.5, "gap": False}, {"key": "2024C", "cu_cap": 5.5, "gap": False}],
            pins=[],
        )
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_zero_and_negative_caps_are_rejected(self):
        for cap in (0, -1):
            with self.assertRaises(PackError):
                pack({"items": []}, [{"key": "2024C", "cu_cap": cap, "gap": False}], pins=[])

    def test_duplicate_semester_keys_are_rejected(self):
        with self.assertRaises(PackError):
            pack(
                {"items": []},
                [{"key": "2024C", "cu_cap": 4, "gap": False}, {"key": "2024C", "cu_cap": 5, "gap": False}],
                pins=[],
            )

    def test_summer_is_used_only_when_allowed(self):
        body = semesters("2024B", "2025A")
        skipped = pack({"items": [item()]}, body, allow_summer=False, pins=[])
        self.assertEqual(skipped["placements"][0]["semester"], "2025A")
        used = pack({"items": [item()]}, body, allow_summer=True, pins=[])
        self.assertEqual(used["placements"][0]["semester"], "2024B")

    def test_synthetic_terms_include_summer_only_when_it_is_allowed(self):
        tight = [{"key": "2024A", "cu_cap": 0.5, "gap": False}]
        without = pack({"items": [item(cu=1)]}, tight, allow_summer=False, pins=[])
        with_summer = pack({"items": [item(cu=1)]}, tight, allow_summer=True, pins=[])
        self.assertEqual(without["placements"][0]["semester"], "2024C")
        self.assertEqual(with_summer["placements"][0]["semester"], "2024B")
        self.assertEqual(next_semester("2024A", True), "2024B")
        self.assertEqual(next_semester("2024B", True), "2024C")

    def test_the_current_semester_is_not_a_place_for_suggestions(self):
        result = pack({"items": [item()]}, semesters("2023C", "2024A"), pins=[])
        self.assertEqual(result["placements"][0]["semester"], "2024A")

    def test_a_past_pin_does_not_shrink_a_future_term(self):
        result = pack(
            {"items": [item()]},
            semesters("2024C", cap=1),
            pins=[{"semester": "2022C", "cu": 5, "full_code": "CIS-0001"}],
        )
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_lower_course_numbers_take_the_earlier_seat(self):
        rows = [
            item(code="CIS-3200", slot="slot:1:1", number=3200),
            item(code="CIS-1200", slot="slot:1:0", number=1200),
        ]
        result = pack({"items": rows}, semesters("2024C", "2025A", cap=1), pins=[])
        self.assertEqual(result["placements"][0]["full_code"], "CIS-1200")
        self.assertEqual(result["placements"][0]["semester"], "2024C")
        self.assertEqual(result["placements"][1]["semester"], "2025A")

    def test_an_unscheduled_course_is_seated_before_a_new_suggestion(self):
        rows = [
            item(kind="course", code="CIS-1000", slot="slot:2:0", number=1000),
            item(kind="placement", code="CIS-9999", number=9999),
        ]
        result = pack({"items": rows}, semesters("2024C", "2025A", cap=1), pins=[])
        self.assertEqual(result["placements"][0]["kind"], "placement")
        self.assertEqual(result["placements"][0]["semester"], "2024C")
        self.assertEqual(result["placements"][1]["semester"], "2025A")

    def test_placeholders_wait_behind_courses(self):
        rows = [
            item(kind="placeholder", code=None, slot="slot:9:0", number=10**9),
            item(kind="course", code="CIS-1200", slot="slot:1:0", number=1200),
        ]
        result = pack({"items": rows}, semesters("2024C", "2025A", cap=1), pins=[])
        self.assertEqual(by_semester(result)["2024C"][0]["kind"], "course")
        self.assertEqual(by_semester(result)["2025A"][0]["kind"], "placeholder")

    def test_generated_cu_sums_only_what_landed(self):
        result = pack(
            {"items": [item(cu=1, slot="slot:1:0"), item(cu=0.5, slot="slot:1:1", number=2), item(cu=6, slot="slot:1:2", number=3)]},
            semesters("2024C"),
            pins=[],
        )
        self.assertAlmostEqual(result["generated_cu"], 1.5)
        self.assertEqual(len(result["unplaced"]), 1)

    def test_a_gap_in_the_middle_is_skipped(self):
        result = pack(
            {"items": [item()]},
            semesters("2024C", "2025A", "2025C", gap=("2024C",)),
            pins=[],
        )
        self.assertEqual(result["placements"][0]["semester"], "2025A")

    def test_the_schedule_stops_after_eight_extra_terms(self):
        rows = [item(code=f"CIS-{i}", slot=f"slot:1:{i}", number=i) for i in range(41)]
        result = pack({"items": rows}, semesters(TEST_SEMESTER), pins=[])
        self.assertEqual(len(result["semesters"]), 8)
        self.assertEqual(len(result["placements"]), 40)
        self.assertEqual(len(result["unplaced"]), 1)
        self.assertTrue(all(not row["semester"].endswith("B") for row in result["placements"]))


class OpenSlotEdgeTests(TestCase):
    def setUp(self):
        use_semester()
        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="EDGE", year=2026)
        self.plan = plan_for(self.degree, username="edge-slots")

    def test_a_degree_with_no_rules_has_no_slots(self):
        self.assertEqual(open_slots(self.plan), [])
        self.assertEqual(suggest(self.plan)["items"], [])

    def test_a_leaf_with_neither_a_count_nor_credits_emits_nothing(self):
        self.degree.rules.add(leaf("Noted", Q(full_code="CIS-1200")))
        self.assertEqual(open_slots(self.plan), [])

    def test_a_credit_only_rule_keeps_a_trailing_half(self):
        rule = leaf("Lab sequence", Q(department__code="LAB"), credits=Decimal("2.5"))
        self.degree.rules.add(rule)
        slots = [slot for slot in open_slots(self.plan) if slot.rule_id == rule.id]
        self.assertEqual([slot.cu for slot in slots], [Decimal("1"), Decimal("1"), Decimal("0.5")])

    def test_meeting_the_count_but_not_the_credits_leaves_the_credit_remainder(self):
        course("LAB-1000")
        rule = leaf("Two CU intro", Q(full_code="LAB-1000"), num=1, credits=Decimal("2"))
        self.degree.rules.add(rule)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="LAB-1000", semester="2023C"
        )
        fulfillment.rules.add(rule)
        slots = [slot for slot in open_slots(self.plan) if slot.rule_id == rule.id]
        self.assertEqual([slot.cu for slot in slots], [Decimal("1")])

    def test_meeting_the_credits_but_not_the_count_leaves_another_course(self):
        course("LAB-1000")
        rule = leaf("Two intros", Q(department__code="LAB"), num=2, credits=Decimal("1"))
        self.degree.rules.add(rule)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="LAB-1000", semester="2023C"
        )
        fulfillment.rules.add(rule)
        slots = [slot for slot in open_slots(self.plan) if slot.rule_id == rule.id]
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].cu, Decimal("1"))

    def test_an_all_of_group_emits_every_child_until_each_is_done(self):
        parent = group("Core")
        first = leaf("A", Q(full_code="AAA-1000"), num=1, parent=parent)
        second = leaf("B", Q(full_code="BBB-1000"), num=1, parent=parent)
        self.degree.rules.add(parent)
        course("AAA-1000")
        self.assertCountEqual(
            [slot.rule_id for slot in open_slots(self.plan)],
            [first.id, second.id],
        )
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="AAA-1000", semester="2023C"
        )
        fulfillment.rules.add(first)
        self.assertEqual([slot.rule_id for slot in open_slots(self.plan)], [second.id])

    def test_finishing_the_chosen_branch_does_not_open_the_other_branch(self):
        parent = group("Pick one", num=1)
        chosen = leaf("Chosen", Q(full_code="AAA-1000"), num=1, parent=parent)
        other = leaf("Other", Q(full_code="BBB-1000"), num=1, parent=parent)
        self.degree.rules.add(parent)
        course("AAA-1000")
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="AAA-1000", semester="2023C"
        )
        fulfillment.rules.add(chosen)
        rule_ids = {slot.rule_id for slot in open_slots(self.plan)}
        self.assertNotIn(chosen.id, rule_ids)
        self.assertNotIn(other.id, rule_ids)

    def test_partial_progress_commits_the_later_child(self):
        parent = group("Pick one sequence", num=1)
        early = leaf("Early", Q(full_code="AAA-1000"), num=2, parent=parent)
        later = leaf("Later", Q(full_code="BBB-1000"), num=2, parent=parent)
        self.degree.rules.add(parent)
        course("BBB-1000")
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="BBB-1000", semester="2023C"
        )
        fulfillment.rules.add(later)
        slots = open_slots(self.plan)
        self.assertEqual([slot.rule_id for slot in slots], [later.id])
        self.assertNotIn(early.id, {slot.rule_id for slot in slots})
        self.assertEqual(len(slots), 1)

    def test_two_degrees_both_contribute_slots(self):
        left = leaf("Left", Q(full_code="AAA-1000"), num=1)
        self.degree.rules.add(left)
        other = Degree.objects.create(program="WU_BS", degree="BS", major="EDG2", year=2026)
        right = leaf("Right", Q(full_code="BBB-1000"), num=1)
        other.rules.add(right)
        self.plan.degrees.add(other)
        self.assertCountEqual(
            [slot.rule_id for slot in open_slots(self.plan)],
            [left.id, right.id],
        )

    def test_a_fulfillment_on_one_degree_does_not_rename_the_other_degrees_slots(self):
        left = leaf("Left", Q(full_code="AAA-1000"), num=2)
        self.degree.rules.add(left)
        before = [slot.slot_id for slot in open_slots(self.plan) if slot.rule_id == left.id]
        other = Degree.objects.create(program="WU_BS", degree="BS", major="EDG3", year=2026)
        right = leaf("Right", Q(full_code="BBB-1000"), num=1)
        other.rules.add(right)
        self.plan.degrees.add(other)
        course("BBB-1000")
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="BBB-1000", semester="2023C"
        )
        fulfillment.rules.add(right)
        after = [slot.slot_id for slot in open_slots(self.plan) if slot.rule_id == left.id]
        self.assertEqual(before, after)
        self.assertEqual(before, [f"slot:{left.id}:0", f"slot:{left.id}:1"])


class SuggestAndScheduleEdgeTests(TestCase):
    def setUp(self):
        use_semester()
        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="SUGG", year=2026
        )
        self.plan = plan_for(self.degree, username="edge-suggest")

    def test_a_choice_of_two_courses_stays_a_stub(self):
        course("TIE-1000", quality=2, difficulty=3)
        course("TIE-2000", quality=2, difficulty=1)
        self.degree.rules.add(
            leaf("Tie", Q(full_code="TIE-1000") | Q(full_code="TIE-2000"), num=1)
        )
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertIsNone(ghost["full_code"])
        self.assertEqual(ghost["short_label"], "TIE 1000/TIE 2000")
        self.assertEqual(set(ghost["alternatives"]), {"TIE-1000", "TIE-2000"})

    def test_a_claim_past_the_sharing_cap_stays_on_the_schedule(self):
        # The course already counts for two degrees. A third match is allowed by
        # double counting and refused by the sharing cap, so the requirement stays.
        course("CIS-1200")
        one = leaf("One", Q(full_code="CIS-1200"), num=1)
        two = leaf("Two", Q(full_code="CIS-1200"), num=1)
        three = leaf("Three", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(one)
        second = Degree.objects.create(program="WU_BS", degree="BS", major="TWO", year=2026)
        third = Degree.objects.create(program="NU_BSN", degree="BSN", major="THR", year=2026)
        second.rules.add(two)
        third.rules.add(three)
        self.plan.degrees.add(second, third)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2023C"
        )
        fulfillment.rules.add(one, two)
        items = suggest(self.plan)["items"]
        self.assertTrue(any(three.id in row["rules"] for row in items))

    def test_a_department_restriction_stays_a_stub(self):
        course("DEPT-1000", quality=1)
        course("DEPT-2000", quality=3)
        self.degree.rules.add(leaf("Dept", Q(department__code="DEPT"), num=1))
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertIsNone(ghost["full_code"])
        self.assertEqual(ghost["short_label"], "DEPT")

    def test_a_level_floor_stays_a_stub(self):
        course("RNG-1090", quality=9)
        course("RNG-2100", quality=1)
        self.degree.rules.add(
            leaf("Upper", Q(department__code="RNG", code__gte="2000"), num=1)
        )
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertEqual(ghost["short_label"], "RNG 2000+")
        self.assertIsNone(ghost["full_code"])

    def test_a_sole_course_outside_the_recency_window_is_not_scheduled(self):
        course("OLD-1000", semester="2019C", quality=9)
        self.degree.rules.add(leaf("Window", Q(full_code="OLD-1000"), num=1))
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertIsNone(ghost["full_code"])

    def test_several_slots_on_one_restriction_stay_stubs(self):
        for code in ("DEPT-1000", "DEPT-1010", "DEPT-1020"):
            course(code)
        self.degree.rules.add(leaf("Three", Q(department__code="DEPT"), num=3))
        ghosts = suggest(self.plan)["items"]
        self.assertEqual(len(ghosts), 3)
        self.assertTrue(all(row["kind"] == "placeholder" and row["full_code"] is None for row in ghosts))

    def test_a_half_credit_course_is_suggested_at_half_a_cu(self):
        course("LAB-1500", credits=0.5)
        self.degree.rules.add(leaf("Lab", Q(full_code="LAB-1500"), num=1))
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["cu"], 0.5)

    def test_a_course_already_on_the_plan_is_not_suggested_for_a_second_rule(self):
        course("CIS-1000")
        course("CIS-1001")
        taken = leaf("First", Q(full_code="CIS-1000"), num=1)
        still_open = leaf(
            "Second",
            Q(full_code="CIS-1000") | Q(full_code="CIS-1001"),
            num=1,
        )
        self.degree.rules.add(taken, still_open)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1000", semester="2023C"
        )
        fulfillment.rules.add(taken)
        ghosts = [row for row in suggest(self.plan)["items"] if still_open.id in row["rules"]]
        self.assertEqual(len(ghosts), 1)
        self.assertEqual(ghosts[0]["kind"], "placeholder")
        self.assertIsNone(ghosts[0]["full_code"])
        self.assertEqual(ghosts[0]["short_label"], "CIS 1000/CIS 1001")

    def test_an_unmatched_rule_stays_a_placeholder_named_for_the_rule(self):
        self.degree.rules.add(leaf("Nothing here", Q(full_code="NOPE-0000"), num=1))
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertEqual(ghost["label"], "Nothing here")
        self.assertIsNone(ghost["full_code"])

    def test_business_breadth_is_a_stub_and_does_not_take_a_specific_course(self):
        course("ACCT-1010")
        course("FNCE-1000")
        course("CIS-1200")
        breadth = leaf(
            "Business Breadth",
            Q(department__code="ACCT") | Q(department__code="FNCE"),
            num=1,
        )
        named = leaf("Programming", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(breadth, named)
        items = suggest(self.plan)["items"]
        stub = next(item for item in items if breadth.id in item["rules"])
        self.assertEqual(stub["kind"], "placeholder")
        self.assertEqual(stub["short_label"], "WH Business Breadth")
        self.assertIsNone(stub["full_code"])
        named_item = next(item for item in items if named.id in item["rules"])
        self.assertEqual(named_item["full_code"], "CIS-1200")

    def test_a_finished_requirement_is_not_suggested_again(self):
        course("CIS-1200")
        rule = leaf("Done", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(rule)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2023C"
        )
        fulfillment.rules.add(rule)
        self.assertEqual(suggest(self.plan)["items"], [])

    def test_an_unscheduled_fulfillment_is_packed_into_the_first_future_term(self):
        course("CIS-1200")
        rule = leaf("Core", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(rule)
        Fulfillment.objects.create(degree_plan=self.plan, full_code="CIS-1200", semester=None)
        result = generate_schedule(self.plan, semesters("2024C", "2025A"))
        self.assertEqual(len(result["placements"]), 1)
        self.assertEqual(result["placements"][0]["kind"], "placement")
        self.assertEqual(result["placements"][0]["semester"], "2024C")
        self.assertEqual(result["placements"][0]["full_code"], "CIS-1200")

    def test_a_future_fulfillment_occupies_its_term(self):
        course("CIS-1100")
        course("CIS-1200")
        placed = leaf("Placed", Q(full_code="CIS-1100"), num=1)
        still_open = leaf("Open", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(placed, still_open)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1100", semester="2024C"
        )
        fulfillment.rules.add(placed)
        result = generate_schedule(self.plan, semesters("2024C", "2025A", cap=1))
        suggestion = next(row for row in result["placements"] if row["full_code"] == "CIS-1200")
        self.assertEqual(suggestion["semester"], "2025A")

    def test_transfer_credit_does_not_consume_a_future_terms_cap(self):
        course("CIS-1100")
        course("CIS-1200")
        transferred = leaf("Transferred", Q(full_code="CIS-1100"), num=1)
        still_open = leaf("Open", Q(full_code="CIS-1200"), num=1)
        self.degree.rules.add(transferred, still_open)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1100", semester="_TRAN"
        )
        fulfillment.rules.add(transferred)
        result = generate_schedule(self.plan, semesters("2024C", cap=1))
        self.assertEqual(result["placements"][0]["full_code"], "CIS-1200")
        self.assertEqual(result["placements"][0]["semester"], "2024C")

    def test_generation_does_not_move_a_course_the_student_already_placed(self):
        course("CIS-1200")
        course("CIS-1600")
        self.degree.rules.add(
            leaf("A", Q(full_code="CIS-1200"), num=1),
            leaf("B", Q(full_code="CIS-1600"), num=1),
        )
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2025A"
        )
        generate_schedule(self.plan, semesters("2024C", "2025A"))
        fulfillment.refresh_from_db()
        self.assertEqual(fulfillment.semester, "2025A")

    def test_a_mixed_plan_covers_every_open_slot_once(self):
        course("CIS-1200")
        course("LAB-1500", credits=0.5)
        for code in ("DEPT-1000", "DEPT-1010"):
            course(code)
        named = leaf("Named", Q(full_code="CIS-1200"), num=1)
        lab = leaf("Lab", Q(full_code="LAB-1500"), num=1)
        electives = leaf("Electives", Q(department__code="DEPT"), num=2)
        missing = leaf("Missing", Q(full_code="NOPE-0000"), num=1)
        self.degree.rules.add(named, lab, electives, missing)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2024C"
        )
        fulfillment.rules.add(named)
        result = generate_schedule(
            self.plan,
            semesters("2024C", "2025A", "2025C", gap=("2025A",)),
        )
        covered = [slot for row in result["placements"] for slot in row["slot_ids"]]
        uncovered = [row["slot_id"] for row in result["unplaced"] if row["slot_id"]]
        self.assertEqual(len(covered), len(set(covered)))
        self.assertEqual(len(covered) + len(uncovered), result["open_rule_count"])
        self.assertNotIn("CIS-1200", {row["full_code"] for row in result["placements"]})
        self.assertNotIn("2025A", {row["semester"] for row in result["placements"]})
        self.assertTrue(all(row["semester"] > TEST_SEMESTER for row in result["placements"]))


class _Rule:
    def __init__(self, q, title=""):
        self.q = repr(q) if q is not None else ""
        self.title = title

    @property
    def q_json(self):
        if not self.q:
            return None
        return json_parser.parse(self.q)


class ScheduleCodeTests(SimpleTestCase):
    def test_one_course_is_its_code(self):
        rule = _Rule(Q(full_code="CIS-1100"), title="Programming Languages and Techniques I")
        self.assertEqual(schedule_code(rule), "CIS 1100")

    def test_two_courses_are_joined(self):
        rule = _Rule(Q(full_code="CIS-1100") | Q(full_code="CIS-1200"), title="Intro")
        self.assertEqual(schedule_code(rule), "CIS 1100/CIS 1200")

    def test_a_longer_course_list_keeps_two_and_a_count(self):
        codes = ["CIS-1100", "CIS-1200", "CIS-1600", "CIS-1210"]
        rule = _Rule(Q(full_code__in=codes), title="Choose a CIS intro")
        self.assertEqual(schedule_code(rule), "CIS")

    def test_a_department_and_level_become_a_short_code(self):
        rule = _Rule(
            Q(department__code="ESE", code__gte="2000"),
            title="Intermediate or Advanced ESE Elective",
        )
        self.assertEqual(schedule_code(rule), "ESE 2000+")

    def test_several_departments_are_joined(self):
        rule = _Rule(
            Q(department__code__in=["MATH", "PHYS", "CHEM"]),
            title="Math, Science, or Engineering Electives",
        )
        self.assertEqual(schedule_code(rule), "MATH/PHYS/CHEM")

    def test_attributes_and_a_closed_level_range_are_kept(self):
        rule = _Rule(
            Q(attributes__code__in=["W"], code__gte="2000", code__lte="4999"),
            title="Critical Writing Seminar",
        )
        self.assertEqual(schedule_code(rule), "W 2000–4999")

    def test_an_open_upper_bound_is_dropped(self):
        rule = _Rule(Q(department__code="MATH", code__gte="1400", code__lte="9999"), title="Math Elective")
        self.assertEqual(schedule_code(rule), "MATH 1400+")

    def test_business_breadth_keeps_its_own_stub(self):
        rule = _Rule(
            Q(department__code__in=["ACCT", "FNCE", "MGMT", "MKTG"]),
            title="Business Breadth",
        )
        self.assertEqual(schedule_code(rule), "WH Business Breadth")

    def test_an_unrestricted_elective_uses_its_query(self):
        rule = _Rule(Q(department__code="CIS"), title="Unrestricted Electives")
        self.assertEqual(schedule_code(rule), "CIS")

    def test_a_rule_with_no_query_keeps_a_short_title(self):
        rule = _Rule(None, title="Math Elective")
        self.assertEqual(schedule_code(rule), "Math Elective")


def _scheduled_cu(result):
    item_cu = sum((Decimal(str(item["cu"])) for item in result["items"]), Decimal(0))
    pin_cu = sum((Decimal(str(pin["cu"])) for pin in result["pins"]), Decimal(0))
    return item_cu + pin_cu


class CreditGapTests(TestCase):
    """Leftover credits are not filled with invented elective cards."""

    def setUp(self):
        use_semester()

    def test_a_credit_gap_is_left_empty(self):
        course("CIS-1200")
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="PAD1", year=2026, credits=Decimal("3")
        )
        degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        result = suggest(plan_for(degree, username="pad-short"))
        self.assertEqual([item["short_label"] for item in result["items"]], ["CIS 1200"])
        self.assertEqual(_scheduled_cu(result), Decimal("1"))

    def test_a_degree_already_at_its_total_schedules_only_its_rules(self):
        course("CIS-1200")
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="PAD2", year=2026, credits=Decimal("1")
        )
        degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        result = suggest(plan_for(degree, username="pad-full"))
        self.assertEqual([item["short_label"] for item in result["items"]], ["CIS 1200"])
        self.assertEqual(_scheduled_cu(result), Decimal("1"))

    def test_a_fractional_shortfall_is_not_filled(self):
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="PAD3", year=2026, credits=Decimal("2.5")
        )
        result = suggest(plan_for(degree, username="pad-frac"))
        self.assertEqual(result["items"], [])
        self.assertEqual(_scheduled_cu(result), Decimal("0"))

    def test_a_ruleless_course_does_not_grow_an_elective_card(self):
        course("CIS-1200")
        course("ELEC-1000")
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="PAD4", year=2026, credits=Decimal("3")
        )
        degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        degree_plan = plan_for(degree, username="pad-loose")
        Fulfillment.objects.create(
            degree_plan=degree_plan, full_code="ELEC-1000", semester="2023C"
        )
        result = suggest(degree_plan)
        self.assertFalse(any(item["rules"] == [] for item in result["items"]))
        self.assertEqual(_scheduled_cu(result), Decimal("2"))

    def test_each_degree_keeps_only_its_shared_course(self):
        course("BOTH-1000")
        left = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="PADL", year=2026, credits=Decimal("2")
        )
        right = Degree.objects.create(
            program="WU_BS", degree="BS", major="PADR", year=2026, credits=Decimal("2")
        )
        left_rule = leaf("Left", Q(full_code="BOTH-1000"), num=1)
        right_rule = leaf("Right", Q(full_code="BOTH-1000"), num=1)
        left.rules.add(left_rule)
        right.rules.add(right_rule)
        degree_plan = plan_for(left, username="pad-dual")
        degree_plan.degrees.add(right)
        fulfillment = Fulfillment.objects.create(
            degree_plan=degree_plan, full_code="BOTH-1000", semester="2023C"
        )
        fulfillment.rules.add(left_rule, right_rule)
        result = suggest(degree_plan)
        self.assertEqual(result["items"], [])
        self.assertEqual(_scheduled_cu(result), Decimal("1"))


def _attribute(code):
    row, _ = Attribute.objects.get_or_create(
        code=code, defaults={"description": code, "school": "SAS"}
    )
    return row


def _gen_ed(block_title, title, query):
    block = Rule.objects.create(title=block_title)
    rule = leaf(title, query, num=1, parent=block)
    return block, rule


class CoverageLabelTests(TestCase):
    """Sectors and foundational approaches are labels, capped by the degree total."""

    def setUp(self):
        use_semester()

    def _plan(self, credits, username):
        course("CIS-1200")
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="COV", year=2026, credits=Decimal(credits)
        )
        core = leaf("Core", Q(full_code="CIS-1200"), num=1)
        degree.rules.add(core)
        degree_plan = plan_for(degree, username=username)
        return degree, degree_plan, core

    def test_a_sector_does_not_add_a_course_past_the_degree_total(self):
        degree, degree_plan, core = self._plan("1", "cov-full")
        block, sector = _gen_ed("General Education, Sectors", "Society", Q(attributes__code__in=["AUSO"]))
        degree.rules.add(block)
        items = suggest(degree_plan)["items"]
        self.assertEqual([item["rules"] for item in items], [[core.id]])
        self.assertNotIn(sector.id, {rule_id for item in items for rule_id in item["rules"]})

    def test_an_open_sector_fills_the_credit_gap(self):
        degree, degree_plan, _core = self._plan("2", "cov-gap")
        block, sector = _gen_ed("General Education, Sectors", "Society", Q(attributes__code__in=["AUSO"]))
        degree.rules.add(block)
        items = suggest(degree_plan)["items"]
        self.assertEqual([item["short_label"] for item in items], ["CIS 1200", "Society"])
        self.assertEqual(sum(Decimal(str(item["cu"])) for item in items), Decimal("2"))
        self.assertEqual(items[1]["rules"], [sector.id])
        self.assertIsNone(items[1]["full_code"])

    def test_credits_past_the_open_labels_are_left_empty(self):
        degree, degree_plan, _core = self._plan("3", "cov-free")
        block, _sector = _gen_ed("General Education, Sectors", "Society", Q(attributes__code__in=["AUSO"]))
        degree.rules.add(block)
        items = suggest(degree_plan)["items"]
        self.assertEqual([item["short_label"] for item in items], ["CIS 1200", "Society"])

    def test_a_course_in_the_degree_carries_a_matching_label(self):
        degree, degree_plan, _core = self._plan("2", "cov-carry")
        course("CIS-1200").attributes.add(_attribute("AUSO"))
        society_block, _society = _gen_ed(
            "General Education, Sectors", "Society", Q(attributes__code__in=["AUSO"])
        )
        history_block, history = _gen_ed(
            "General Education, Sectors", "History", Q(attributes__code__in=["AUHT"])
        )
        degree.rules.add(society_block, history_block)
        items = suggest(degree_plan)["items"]
        self.assertEqual([item["short_label"] for item in items], ["CIS 1200", "History"])
        self.assertEqual(items[1]["rules"], [history.id])

    def test_a_course_carries_at_most_two_labels(self):
        degree, degree_plan, _core = self._plan("2", "cov-two")
        row = course("CIS-1200")
        for code in ("AUSO", "AUHT", "AUAL"):
            row.attributes.add(_attribute(code))
        blocks = []
        for title, code in (("Society", "AUSO"), ("History", "AUHT"), ("Arts", "AUAL")):
            block, _rule = _gen_ed(
                "General Education, Sectors", title, Q(attributes__code__in=[code])
            )
            blocks.append(block)
        degree.rules.add(*blocks)
        items = suggest(degree_plan)["items"]
        self.assertEqual(items[0]["short_label"], "CIS 1200")
        self.assertEqual(len(items), 2)
        self.assertTrue(items[1]["rules"])
        self.assertIn(items[1]["short_label"], {"Society", "History", "Arts"})

    def test_writing_stays_a_course_when_a_sector_does_not_fit(self):
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="COV", year=2026, credits=Decimal("1")
        )
        writing_block, writing = _gen_ed(
            "General Education, Foundations", "Writing Course", Q(department__code="WRIT")
        )
        sector_block, sector = _gen_ed(
            "General Education, Sectors", "Society", Q(attributes__code__in=["AUSO"])
        )
        degree.rules.add(writing_block, sector_block)
        items = suggest(plan_for(degree, username="cov-writ"))["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["rules"], [writing.id])
        self.assertNotIn(sector.id, items[0]["rules"])


class PanelOptionsTests(TestCase):
    def setUp(self):
        use_semester()

    def test_a_short_restriction_lists_its_courses(self):
        for code in ("CHEM-1012", "BIOL-1101", "BIOL-1121"):
            course(code)
        rule = leaf("Chemistry or Biology", Q(department__code__in=["CHEM", "BIOL"]))
        options = filter_panel_options(rule)
        self.assertEqual(options["count"], 3)
        self.assertCountEqual(options["courses"], ["CHEM-1012", "BIOL-1101", "BIOL-1121"])

    def test_a_large_restriction_is_only_a_count(self):
        for offset in range(9):
            course(f"STAT-{4000 + offset}")
        rule = leaf("Statistics", Q(department__code="STAT"))
        options = filter_panel_options(rule)
        self.assertGreater(options["count"], 8)
        self.assertNotIn("courses", options)

    def test_an_explicit_course_list_is_left_to_the_panel(self):
        rule = leaf("Pick", Q(full_code="CIS-1100") | Q(full_code="CIS-1200"))
        self.assertIsNone(filter_panel_options(rule))

class OverlapAndReconcileTests(TestCase):
    def setUp(self):
        use_semester()

    def _pair(self, username, query, left_title, right_title):
        left = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="OLP", year=2026, credits=Decimal("1")
        )
        right = Degree.objects.create(
            program="WU_BS", degree="BS", major="OLW", year=2026, credits=Decimal("1")
        )
        left.rules.add(leaf(left_title, query, num=1))
        right.rules.add(leaf(right_title, query, num=1))
        degree_plan = plan_for(left, username=username)
        degree_plan.degrees.add(right)
        return generate_schedule(degree_plan, semesters("2024C", "2025A"))

    def test_a_shared_course_list_becomes_one_card(self):
        course("CIS-1000")
        course("CIS-1001")
        query = Q(full_code="CIS-1000") | Q(full_code="CIS-1001")
        result = self._pair("overlap-list", query, "Engineering list", "Wharton list")
        overlaps = [row for row in result["placements"] if row.get("overlap")]
        self.assertEqual(len(overlaps), 1)
        self.assertCountEqual(overlaps[0]["alternatives"], ["CIS-1000", "CIS-1001"])
        self.assertEqual(len(overlaps[0]["rules"]), 2)
        self.assertEqual(overlaps[0]["cu"], 1.0)

    def test_department_electives_stay_separate(self):
        for offset in range(3):
            course(f"CIS-{2000 + offset}")
        result = self._pair(
            "overlap-dept",
            Q(department__code="CIS"),
            "Engineering elective",
            "Wharton elective",
        )
        self.assertFalse(any(row.get("overlap") for row in result["placements"]))

    def test_a_second_spelling_is_removed_and_claims_cover_both_programs(self):
        primary = course("ACCT-2110")
        other = course("BEPP-2110")
        other.primary_listing = primary
        other.save()
        course("MATH-1400")
        left = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="XLP", year=2026, credits=Decimal("1")
        )
        right = Degree.objects.create(
            program="WU_BS", degree="BS", major="XLW", year=2026, credits=Decimal("1")
        )
        calculus = leaf("Calculus", Q(full_code="MATH-1400"), num=1)
        math = leaf("Math", Q(full_code="MATH-1400"), num=1)
        left.rules.add(calculus)
        right.rules.add(math)
        degree_plan = plan_for(left, username="xlist")
        degree_plan.degrees.add(right)
        Fulfillment.objects.create(degree_plan=degree_plan, full_code="ACCT-2110", semester="2023C")
        Fulfillment.objects.create(degree_plan=degree_plan, full_code="BEPP-2110", semester="2024C")
        kept = Fulfillment.objects.create(
            degree_plan=degree_plan, full_code="MATH-1400", semester="2023C"
        )
        kept.rules.add(math)
        from degree.utils.generation.reconcile import mutex_violations, prepare_plan

        prepared = prepare_plan(degree_plan)
        remaining = set(Fulfillment.objects.filter(degree_plan=degree_plan).values_list("full_code", flat=True))
        self.assertEqual(remaining, {"ACCT-2110", "MATH-1400"})
        self.assertEqual(prepared["removed"][0]["kind"], "also_offered")
        self.assertTrue(prepared["claims_updated"])
        claimed = set(
            Fulfillment.objects.get(degree_plan=degree_plan, full_code="MATH-1400").rules.values_list(
                "id", flat=True
            )
        )
        self.assertEqual(claimed, {calculus.id, math.id})

        course("ACCT-2420")
        course("ACCT-7420")
        Fulfillment.objects.create(degree_plan=degree_plan, full_code="ACCT-2420", semester="2024C")
        Fulfillment.objects.create(degree_plan=degree_plan, full_code="ACCT-7420", semester="2025A")
        kinds = {row["kind"] for row in mutex_violations(degree_plan)}
        self.assertIn("mutually_exclusive", kinds)
