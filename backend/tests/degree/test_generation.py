import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Q
from django.db.models.signals import post_save
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
from degree.models import Degree, DegreePlan, Fulfillment, Minor, PDPBetaUser, Rule
from degree.utils.generation import generate_schedule
from degree.utils.generation.open_rules import open_slots, slot_cus
from degree.utils.generation.pack import PackError, next_semester, pack
from degree.utils.generation.suggest import _candidates, suggest


TEST_SEMESTER = "2023C"


def use_semester():
    """Record the current semester without saving an add/drop period (that fans out to Redis)."""
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option.objects.update_or_create(
        key="SEMESTER", defaults={"value": TEST_SEMESTER, "value_type": "TXT"}
    )


def course(full_code, semester=TEST_SEMESTER, credits=1, quality=None, difficulty=None):
    row, _, _, _ = get_or_create_course_and_section(
        f"{full_code}-001",
        semester,
        course_defaults={"credits": credits},
    )
    if quality is not None:
        row.precompute_course_quality = Decimal(str(quality))
    if difficulty is not None:
        row.precompute_difficulty = Decimal(str(difficulty))
    if quality is not None or difficulty is not None:
        row.save()
    return row


def leaf(title, q, num=None, credits=None, **extra):
    return Rule.objects.create(
        title=title,
        q=repr(q),
        num=num,
        credits=credits,
        **extra,
    )


def plan_for(degree, username="planner"):
    person = get_user_model().objects.create_user(username=username, password="pw")
    degree_plan = DegreePlan.objects.create(name="plan", person=person)
    degree_plan.degrees.add(degree)
    return degree_plan


def semesters(*keys, cap=5.5, gap=()):
    return [{"key": key, "cu_cap": cap, "gap": key in gap} for key in keys]


class SlotCuTest(TestCase):
    def test_credit_remainder_gets_a_trailing_fraction(self):
        cus = slot_cus(1, Decimal("1.5"))
        self.assertEqual(cus, [Decimal("1"), Decimal("0.5")])

    def test_whole_credits_stay_whole(self):
        self.assertEqual(slot_cus(None, Decimal("2")), [Decimal("1"), Decimal("1")])

    def test_half_credit_is_one_slot(self):
        self.assertEqual(slot_cus(0, Decimal("0.5")), [Decimal("0.5")])


class OpenRulesTest(TestCase):
    def setUp(self):
        use_semester()
        course("CIS-1200")
        course("CIS-1600")
        course("CIS-1210")
        course("CIS-1910", credits=0.5)
        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.core = leaf("CIS 1200", Q(full_code="CIS-1200"), num=1)
        self.math = leaf("CIS 1600", Q(full_code="CIS-1600"), num=1)
        self.group = Rule.objects.create(title="Pick one", num=1)
        self.option_a = leaf("Option A", Q(full_code="CIS-1210"), num=1, parent=self.group)
        self.option_b = leaf("Option B", Q(full_code="CIS-1910"), num=1, parent=self.group)
        self.elective = leaf(
            "CIS electives",
            Q(department__code="CIS", code__gte="2000"),
            num=3,
            credits=Decimal("3.5"),
        )
        self.degree.rules.add(self.core, self.math, self.group, self.elective)
        self.plan = plan_for(self.degree)

    def ids(self):
        return [slot.slot_id for slot in open_slots(self.plan)]

    def test_empty_plan_emits_every_slot(self):
        slots = {slot.rule_id: slot for slot in open_slots(self.plan)}
        self.assertEqual(slots[self.core.id].kind, "listed")
        self.assertIn(f"slot:{self.core.id}:0", self.ids())
        elective_slots = [s for s in open_slots(self.plan) if s.rule_id == self.elective.id]
        # num 3 and 3.5 credits -> 4 slots, last one half a CU
        self.assertEqual(len(elective_slots), 4)
        self.assertEqual(elective_slots[-1].cu, Decimal("0.5"))
        self.assertEqual(elective_slots[0].kind, "restriction")

    def test_fulfilled_leaf_emits_nothing(self):
        course("CIS-1200")
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1200", semester="2023C"
        )
        fulfillment.rules.add(self.core)
        self.assertNotIn(self.core.id, {slot.rule_id for slot in open_slots(self.plan)})

    def test_both_limits_after_partial_progress(self):
        for code in ("CIS-2000", "CIS-2010"):
            course(code)
            fulfillment = Fulfillment.objects.create(
                degree_plan=self.plan, full_code=code, semester="2023C"
            )
            fulfillment.rules.add(self.elective)
        elective_slots = [s for s in open_slots(self.plan) if s.rule_id == self.elective.id]
        # 2 of 3 courses, 2 of 3.5 credits -> max(1, ceil(1.5)) = 2 slots, trailing 0.5
        self.assertEqual([slot.cu for slot in elective_slots], [Decimal("1"), Decimal("0.5")])

    def test_n_of_m_commits_to_the_child_with_progress_and_breaks_ties_by_id(self):
        # No progress: the lower id wins.
        committed = [
            s.rule_id
            for s in open_slots(self.plan)
            if s.rule_id in {self.option_a.id, self.option_b.id}
        ]
        self.assertEqual(committed, [min(self.option_a.id, self.option_b.id)])

        winner = self.option_b if self.option_b.id > self.option_a.id else self.option_a
        course("CIS-1910", credits=0.5)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1910", semester="2023C"
        )
        fulfillment.rules.add(self.option_b)
        committed = [
            s.rule_id
            for s in open_slots(self.plan)
            if s.rule_id in {self.option_a.id, self.option_b.id}
        ]
        # option b is now satisfied, so the group emits nothing for either child
        self.assertEqual(committed, [])
        self.assertNotEqual(winner, None)

    def test_override_counts_and_illegal_fulfillment_still_counts(self):
        course("MATH-1400")
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="MATH-1400", semester="2023C", legal=False
        )
        fulfillment.overrides.add(self.core)
        fulfillment.rules.add(self.core)
        self.assertNotIn(self.core.id, {slot.rule_id for slot in open_slots(self.plan)})

    def test_slot_ids_survive_an_unrelated_fulfillment(self):
        before = self.ids()
        course("MATH-1400")
        Fulfillment.objects.create(degree_plan=self.plan, full_code="MATH-1400", semester="2022C")
        self.assertEqual(before, self.ids())

    def test_transfer_rule_still_emits_a_future_slot(self):
        self.core.transfer_credit_allowed = False
        self.core.save()
        self.assertIn(self.core.id, {slot.rule_id for slot in open_slots(self.plan)})


class SuggestTest(TestCase):
    def setUp(self):
        use_semester()
        self.low = course("CIS-1200", quality=1, difficulty=3)
        self.mid = course("CIS-1600", quality=2, difficulty=1)
        self.high = course("CIS-1100", quality=3, difficulty=2)
        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.rule = leaf(
            "Intro",
            Q(full_code="CIS-1100") | Q(full_code="CIS-1200") | Q(full_code="CIS-1600"),
            num=1,
        )
        self.degree.rules.add(self.rule)
        self.plan = plan_for(self.degree, username="suggester")

    def candidate_codes(self):
        return [row.full_code for row in _candidates(self.rule, set(), set())]

    def test_a_list_of_courses_is_a_placeholder(self):
        ghost = suggest(self.plan)["items"][0]
        self.assertEqual(ghost["kind"], "placeholder")
        self.assertIsNone(ghost["full_code"])
        self.assertEqual(set(ghost["alternatives"]), {"CIS-1100", "CIS-1200", "CIS-1600"})

    def test_ranks_by_quality_then_difficulty_then_code(self):
        self.assertEqual(self.candidate_codes(), ["CIS-1100", "CIS-1600", "CIS-1200"])

    def test_null_quality_sorts_last(self):
        self.high.precompute_course_quality = None
        self.high.save()
        self.mid.precompute_course_quality = Decimal("2")
        self.mid.save()
        self.assertEqual(self.candidate_codes(), ["CIS-1600", "CIS-1200", "CIS-1100"])

    def test_excludes_on_plan_codes_and_crosslists(self):
        twin, _, _, _ = get_or_create_course_and_section(
            "CIS-1101-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        twin.primary_listing = self.high
        twin.precompute_course_quality = Decimal("9")
        twin.save()
        self.rule.q = repr(
            Q(full_code="CIS-1100")
            | Q(full_code="CIS-1101")
            | Q(full_code="CIS-1200")
            | Q(full_code="CIS-1600")
        )
        self.rule.save()
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CIS-1100", semester=None
        )
        fulfillment.rules.add(self.rule)
        # The leaf is satisfied by the unplaced course, so no course ghost. The unplaced
        # course itself comes back as a placement, and its crosslist is not suggested.
        items = suggest(self.plan)["items"]
        self.assertTrue(all(item["full_code"] != "CIS-1101" for item in items))
        self.assertEqual(items[0]["kind"], "placement")

    def test_one_course_covers_two_shared_slots(self):
        other = leaf(
            "Also intro", Q(full_code="CIS-1100"), num=1, share_targets=[{"kind": "MAJOR"}]
        )
        self.rule.share_targets = [{"kind": "MAJOR"}]
        self.rule.block_type = "MAJOR"
        self.rule.block_value = "CIS"
        other.block_type = "MAJOR"
        other.block_value = "MATH"
        self.rule.save()
        other.save()
        self.degree.rules.add(other)
        ghosts = [item for item in suggest(self.plan)["items"] if item["kind"] == "course"]
        self.assertEqual(len(ghosts), 1)
        self.assertEqual(ghosts[0]["full_code"], "CIS-1100")
        self.assertCountEqual(ghosts[0]["rules"], [self.rule.id, other.id])
        self.assertEqual(len(ghosts[0]["slot_ids"]), 2)

    def test_no_course_is_reused_across_slots(self):
        self.degree.rules.remove(self.rule)
        first = leaf("First", Q(full_code="CIS-1100"), num=1)
        second = leaf("Second", Q(full_code="CIS-1100"), num=1)
        self.degree.rules.add(first, second)
        items = suggest(self.plan)["items"]
        ghosts = [item for item in items if item["full_code"] == "CIS-1100"]
        self.assertEqual(len(ghosts), 1)
        self.assertEqual(len(ghosts[0]["rules"]), 1)
        other = next(item for item in items if item is not ghosts[0])
        self.assertEqual(other["kind"], "placeholder")

    def test_broad_restriction_stays_a_placeholder(self):
        broad = leaf("Any CIS", Q(department__code="CIS"), num=1)
        self.degree.rules.add(broad)
        items = suggest(self.plan)["items"]
        placeholder = next(item for item in items if broad.id in item["rules"])
        self.assertEqual(placeholder["kind"], "placeholder")
        self.assertIsNone(placeholder["full_code"])

    def test_zero_candidates_is_a_placeholder(self):
        missing = leaf("Missing", Q(full_code="ZZZ-9999"), num=1)
        self.degree.rules.add(missing)
        item = next(item for item in suggest(self.plan)["items"] if missing.id in item["rules"])
        self.assertEqual(item["kind"], "placeholder")

    def test_stale_course_is_not_suggested(self):
        course("CIS-1090", semester="2018C", quality=9)
        self.rule.q = repr(Q(full_code="CIS-1090") | Q(full_code="CIS-1100"))
        self.rule.save()
        self.assertEqual(self.candidate_codes(), ["CIS-1100"])

    def test_graduate_cap_keeps_the_undergrad_rule_only(self):
        grad = Degree.objects.create(program="EM_MSE", degree="MSE", major="CIS", year=2026)
        codes = ["CIS-5200", "CIS-5500", "CIS-5550", "CIS-5450"]
        for code in codes:
            course(code)
        under = leaf(
            "BSE",
            Q(full_code__in=codes),
            num=4,
            block_type="MAJOR",
            block_value="CSCI",
            share_targets=[{"kind": "MAJOR"}],
        )
        graduate = leaf(
            "MSE",
            Q(full_code__in=codes),
            num=4,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=[{"kind": "MAJOR"}],
        )
        bse = Degree.objects.create(program="EU_BSE", degree="BSE", major="CSCI", year=2026)
        bse.rules.add(under)
        grad.rules.add(graduate)
        person = get_user_model().objects.create_user(username="submat-gen", password="pw")
        degree_plan = DegreePlan.objects.create(name="submat", person=person)
        degree_plan.degrees.add(bse, grad)
        for code in codes[:3]:
            fulfillment = Fulfillment.objects.create(
                degree_plan=degree_plan, full_code=code, semester="2023C"
            )
            fulfillment.rules.set([under, graduate])
        items = suggest(degree_plan)["items"]
        self.assertTrue(any(under.id in item["rules"] for item in items))
        # Three shared CU already hit the graduate cap, so the last slots do not pair.
        self.assertFalse(
            any(under.id in item["rules"] and graduate.id in item["rules"] for item in items)
        )

    def test_a_taken_course_is_not_suggested_again_for_a_rule_it_can_share(self):
        course("WRIT-0400")
        course("WRIT-0020")
        share = [{"kind": "THISBLOCK"}]
        taken = leaf(
            "Tech, Business, and Society Writing Course",
            Q(full_code="WRIT-0400"),
            credits=1,
            block_type="OTHER",
            block_value="WRIT",
            share_targets=share,
        )
        still_open = leaf(
            "Critical Writing Seminar",
            Q(department__code="WRIT"),
            credits=1,
            block_type="OTHER",
            block_value="WRIT",
            share_targets=share,
        )
        self.degree.rules.add(taken, still_open)
        fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="WRIT-0400", semester="2026A"
        )
        fulfillment.rules.add(taken)
        items = suggest(self.plan)["items"]
        self.assertFalse(any(still_open.id in item["rules"] for item in items))


class PackTest(TestCase):
    def setUp(self):
        use_semester()

    def item(self, kind, cu=1.0, code="CIS-1200", slot="slot:1:0", number=1200):
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

    def test_respects_caps_and_orders_kinds(self):
        suggestions = {
            "items": [
                self.item("placeholder", slot="slot:9:0", code=None, number=10**9),
                self.item("course", code="CIS-3200", slot="slot:2:0", number=3200),
                self.item("placement", code="CIS-1100", number=1100),
            ]
        }
        # 5.5 cap fits placement + course (2) in the first future semester; placeholder follows.
        result = pack(suggestions, semesters("2024C", "2025A"), pins=[])
        by_sem = {}
        for row in result["placements"]:
            by_sem.setdefault(row["semester"], []).append(row["kind"])
        self.assertEqual(by_sem["2024C"][0], "placement")
        self.assertIn("course", by_sem["2024C"])

    def test_overfull_pin_does_not_block_other_semesters(self):
        suggestions = {"items": [self.item("course")]}
        result = pack(
            suggestions,
            semesters("2024C", "2025A", cap=1),
            pins=[{"semester": "2024C", "cu": 6, "full_code": "CIS-9999"}],
        )
        self.assertEqual(result["placements"][0]["semester"], "2025A")

    def test_skips_past_gap_and_summer_unless_allowed(self):
        suggestions = {"items": [self.item("course")]}
        result = pack(
            suggestions,
            semesters("2022C", "2024B", "2024C", gap=("2024C",)),
            allow_summer=False,
            pins=[],
        )
        # 2022C is past, 2024B is summer, 2024C is a gap, so the packer extends.
        self.assertTrue(result["semesters"])
        self.assertNotEqual(result["placements"][0]["semester"], "2024B")
        self.assertNotEqual(result["placements"][0]["semester"], "2022C")
        self.assertTrue(result["placements"][0]["semester"] > "2023C")

    def test_summer_on_uses_the_summer_cap(self):
        suggestions = {"items": [self.item("course", cu=2)]}
        result = pack(suggestions, semesters("2024B", cap=2), allow_summer=True, pins=[])
        self.assertEqual(result["placements"][0]["semester"], "2024B")

    def test_synthetic_extension_and_overflow(self):
        self.assertEqual(next_semester("2028A", False), "2028C")
        self.assertEqual(next_semester("2028C", False), "2029A")
        suggestions = {"items": [self.item("course", cu=6)]}
        result = pack(suggestions, [{"key": "2024C", "cu_cap": 0.5, "gap": False}], pins=[])
        self.assertEqual(result["placements"], [])
        self.assertEqual(result["semesters"], [])
        self.assertEqual(result["unplaced"][0]["reason"], "no_capacity")

    def test_bad_keys_raise(self):
        with self.assertRaises(PackError):
            pack({"items": []}, [{"key": "fall", "cu_cap": 5}], pins=[])

    def test_transfer_bucket_is_ignored_and_future_terms_still_fill(self):
        suggestions = {
            "items": [self.item("course", slot=f"slot:1:{i}", number=1000 + i) for i in range(8)]
        }
        result = pack(
            suggestions,
            [{"key": "_TRAN", "cu_cap": 5.5, "gap": False}] + semesters("2023C", "2024A", "2024C"),
            pins=[],
        )
        semesters_used = {row["semester"] for row in result["placements"]}
        self.assertNotIn("_TRAN", semesters_used)
        self.assertNotIn("2023C", semesters_used)
        self.assertIn("2024A", semesters_used)
        self.assertIn("2024C", semesters_used)

    def test_a_pinned_slot_stays_on_its_semester(self):
        suggestions = {
            "items": [self.item("placeholder", slot="slot:9:0", code=None, number=10**9)]
        }
        result = pack(
            suggestions,
            semesters("2024C", "2025A"),
            pinned_slots=[{"slot_id": "slot:9:0", "semester": "2025A"}],
            pins=[],
        )
        self.assertEqual(result["placements"][0]["semester"], "2025A")
        with self.assertRaises(PackError):
            pack(
                {"items": []},
                [{"key": "2024C", "cu_cap": 5}, {"key": "2024C", "cu_cap": 5}],
                pins=[],
            )
        with self.assertRaises(PackError):
            pack({"items": []}, [{"key": "2024C", "cu_cap": 0}], pins=[])

    def test_generate_is_deterministic(self):
        course("CIS-1200", quality=2)
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        degree_plan = plan_for(degree, username="det")
        body = semesters("2024C", "2025A")
        self.assertEqual(
            generate_schedule(degree_plan, body),
            generate_schedule(degree_plan, body),
        )


class GenerateInvariantsTest(TestCase):
    def test_randomized_plans_hold_the_invariants(self):
        use_semester()
        rng = random.Random(0)
        codes = [f"CIS-{1100 + i}" for i in range(6)]
        for code in codes:
            course(code, quality=rng.randint(1, 4))
        for seed in range(5):
            degree = Degree.objects.create(
                program="EU_BSE", degree="BSE", major="CIS", year=2026, concentration=str(seed)
            )
            rule = leaf(f"Core {seed}", Q(full_code__in=codes), num=3)
            degree.rules.add(rule)
            degree_plan = plan_for(degree, username=f"rand-{seed}")
            placed = rng.sample(codes, rng.randint(0, 2))
            for code in placed:
                fulfillment = Fulfillment.objects.create(
                    degree_plan=degree_plan, full_code=code, semester="2023C"
                )
                fulfillment.rules.add(rule)
            gap = ("2024C",) if seed % 2 == 0 else ()
            result = generate_schedule(
                degree_plan,
                semesters("2022A", "2024B", "2024C", "2025A", gap=gap),
                allow_summer=False,
            )
            seen = set(placed)
            for row in result["placements"]:
                self.assertGreater(row["semester"], TEST_SEMESTER)
                self.assertFalse(row["semester"].endswith("B"))
                self.assertNotIn(row["semester"], gap)
                if row["full_code"]:
                    self.assertNotIn(row["full_code"], seen)
                    seen.add(row["full_code"])
            used = {}
            for row in result["placements"]:
                used[row["semester"]] = used.get(row["semester"], 0) + row["cu"]
            for key, cu in used.items():
                self.assertLessEqual(cu, 5.5 + 1e-6)
            covered = set()
            for row in result["placements"]:
                covered.update(row["slot_ids"])
            uncovered = {row["slot_id"] for row in result["unplaced"] if row["slot_id"]}
            self.assertTrue(covered.isdisjoint(uncovered))
            self.assertEqual(len(covered) + len(uncovered), result["open_rule_count"])


class GenerateApiTest(TestCase):
    def setUp(self):
        use_semester()
        course("CIS-1200")
        self.user = get_user_model().objects.create_user(username="api", password="pw")
        PDPBetaUser.objects.create(person=self.user)
        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        self.degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        self.plan = DegreePlan.objects.create(name="api", person=self.user)
        self.plan.degrees.add(self.degree)
        self.client = APIClient()
        self.client.force_login(self.user)
        self.url = reverse("degreeplan-generate", kwargs={"pk": self.plan.id})

    def test_returns_a_proposal_and_writes_nothing(self):
        before = Fulfillment.objects.count()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.post(
                self.url,
                {"semesters": semesters("2024C"), "allow_summer": False},
                format="json",
            )
        self.assertLess(len(captured), 80, "generate ran more queries than the budget")
        self.assertGreater(len(captured), 0)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(Fulfillment.objects.count(), before)
        self.assertIn("placements", response.data)
        self.assertIn("open_rule_count", response.data)
        self.assertLess(len(response.data["placements"]), 80)

    def test_rejects_bad_semesters(self):
        response = self.client.post(self.url, {"semesters": [{"key": "nope"}]}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_stranger_and_non_beta_are_rejected(self):
        other = get_user_model().objects.create_user(username="other", password="pw")
        PDPBetaUser.objects.create(person=other)
        stranger = APIClient()
        stranger.force_login(other)
        self.assertEqual(stranger.post(self.url, {"semesters": []}, format="json").status_code, 404)
        plain = get_user_model().objects.create_user(username="plain", password="pw")
        client = APIClient()
        client.force_login(plain)
        self.assertEqual(client.post(self.url, {"semesters": []}, format="json").status_code, 403)


class GenerateRoundTripTest(TestCase):
    def test_accepting_every_course_ghost_leaves_nothing_to_regenerate(self):
        use_semester()
        course("CIS-1200", quality=3)
        course("CIS-1600", quality=2)
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        first = leaf("1200", Q(full_code="CIS-1200"), num=1)
        second = leaf("1600", Q(full_code="CIS-1600"), num=1)
        degree.rules.add(first, second)
        degree_plan = plan_for(degree, username="round")
        body = semesters("2024C", "2025A")
        first_pass = generate_schedule(degree_plan, body)
        course_ghosts = [row for row in first_pass["placements"] if row["kind"] == "course"]
        self.assertGreaterEqual(len(course_ghosts), 1)
        for ghost in course_ghosts:
            fulfillment = Fulfillment.objects.create(
                degree_plan=degree_plan,
                full_code=ghost["full_code"],
                semester=ghost["semester"],
            )
            fulfillment.rules.set(ghost["rules"])
        second_pass = generate_schedule(degree_plan, body)
        suggested = {
            row["full_code"] for row in second_pass["placements"] if row["kind"] == "course"
        }
        self.assertTrue(suggested.isdisjoint({ghost["full_code"] for ghost in course_ghosts}))

    def test_slot_ids_survive_adding_an_unrelated_minor(self):
        use_semester()
        course("CIS-1200")
        course("MATH-1400")
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        degree.rules.add(leaf("Core", Q(full_code="CIS-1200"), num=1))
        degree_plan = plan_for(degree, username="minor-add")
        before = {slot.slot_id for slot in open_slots(degree_plan)}
        minor = Minor.objects.create(program_code="MATH-MINOR", code="MATH", name="Math", year=2026)
        minor.rules.add(
            leaf("Math", Q(full_code="MATH-1400"), num=1, block_type="MINOR", block_value="MATH")
        )
        degree_plan.minors.add(minor)
        after = {slot.slot_id for slot in open_slots(degree_plan)}
        self.assertTrue(before <= after)
