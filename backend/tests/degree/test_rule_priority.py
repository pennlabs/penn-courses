from unittest.mock import patch

from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase

from courses.util import get_or_create_course_and_section
from degree.management.commands.deduplicate_rules import deduplicate_rules
from degree.models import Degree, Rule
from degree.utils.degree_logic import assign_individual_rule, get_priority_rule

from .test_reparsing_degrees import COMMAND, fetch


SEMESTER = "2024A"


def course(full_code, semester=SEMESTER):
    created, _, _, _ = get_or_create_course_and_section(
        f"{full_code}-001", semester, course_defaults={"credits": 1}
    )
    return created


def rule(title, q, **fields):
    fields.setdefault("num", 1)
    return Rule.objects.create(title=title, q=repr(q), **fields)


class RefreshRuleMatchCountsTest(TestCase):
    def refresh(self):
        call_command("refresh_rule_match_counts", verbosity=0)

    def test_counts_each_course_once_across_semesters(self):
        course("CIS-1200")
        course("CIS-1200", "2024C")
        course("CIS-1600")
        department = rule("CIS", Q(department__code="CIS"))

        self.refresh()

        department.refresh_from_db()
        self.assertEqual(department.match_count, 2)

    def test_leaves_parent_rules_uncounted(self):
        parent = Rule.objects.create(title="Parent", num=1)

        self.refresh()

        parent.refresh_from_db()
        self.assertIsNone(parent.match_count)

    def test_rule_matching_nothing_counts_zero(self):
        empty = rule("Empty", Q(full_code="NONE-0000"))

        self.refresh()

        empty.refresh_from_db()
        self.assertEqual(empty.match_count, 0)

    def test_count_does_not_stop_rules_deduplicating(self):
        degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CSCI", concentration="X", year=2025
        )
        first = rule("Same", Q(full_code="CIS-1200"), match_count=1)
        second = rule("Same", Q(full_code="CIS-1200"), match_count=None)
        degree.rules.add(first, second)

        deduplicate_rules()

        self.assertEqual(Rule.objects.filter(title="Same").count(), 1)


class ImportRefreshesCountsTest(TestCase):
    def leaves(self):
        return Rule.objects.exclude(q="")

    def test_import_counts_every_new_leaf(self):
        fetch()
        self.assertTrue(self.leaves().exists())
        self.assertFalse(self.leaves().filter(match_count__isnull=True).exists())

    def test_reimport_recounts_a_patched_rule(self):
        fetch()
        changed = self.leaves().first()
        Rule.objects.filter(pk=changed.pk).update(q=repr(Q(department__code="X")), match_count=999)

        fetch()

        changed.refresh_from_db()
        self.assertNotEqual(changed.match_count, 999)
        self.assertIsNotNone(changed.match_count)

    def test_dry_run_does_not_refresh(self):
        with patch(f"{COMMAND}.refresh_rule_match_counts") as refresh, patch(
            f"{COMMAND}.PathClient"
        ):
            call_command(
                "fetch_degrees_from_path",
                srcdb=["202630"],
                program=["BIOL-BA"],
                dry_run=True,
                verbosity=0,
            )
        refresh.assert_not_called()


class GetPriorityRuleTest(TestCase):
    FULL_CODE = "CIS-1200"

    def rule(self, title, match_count=None, q=None, **fields):
        return rule(title, q or Q(department__code="CIS"), match_count=match_count, **fields)

    def priority(self, *rules, is_transfer=False, not_belonging=()):
        cache = {(r.id, self.FULL_CODE): r not in not_belonging for r in rules}
        return get_priority_rule(set(rules), self.FULL_CODE, cache, is_transfer=is_transfer)

    def test_prefers_fewest_matches_over_most_credits(self):
        catch_all = self.rule("Arts and Sciences 28 CU", 16000, credits=28, num=None)
        sector = self.rule("Sector", 96)
        self.assertEqual(self.priority(catch_all, sector), sector)

    def test_scarcer_rule_beats_one_naming_the_course(self):
        naming = self.rule("Long list", 300, q=Q(full_code=self.FULL_CODE))
        scarce = self.rule("Scarce", 64)
        self.assertEqual(self.priority(naming, scarce), scarce)

    def test_counted_rule_beats_uncounted(self):
        uncounted = self.rule("Uncounted", None, q=Q(full_code=self.FULL_CODE))
        catch_all = self.rule("Catch-all", 29000)
        self.assertEqual(self.priority(uncounted, catch_all), catch_all)

    def test_ties_go_to_the_rule_naming_the_course(self):
        pool = self.rule("Pool", 5, credits=4, num=None)
        naming = self.rule("Named", 5, q=Q(full_code=self.FULL_CODE))
        self.assertEqual(self.priority(pool, naming), naming)

    def test_uncounted_rules_fall_back_to_most_credits(self):
        small = self.rule("Small", credits=1, num=None)
        large = self.rule("Large", credits=4, num=None)
        self.assertEqual(self.priority(small, large), large)

    def test_remaining_ties_go_to_lowest_id(self):
        first = self.rule("First", 5)
        second = self.rule("Second", 5)
        self.assertEqual(self.priority(second, first), first)

    def test_skips_rule_the_course_does_not_belong_to(self):
        scarce = self.rule("Scarce", 1)
        broad = self.rule("Broad", 1000)
        self.assertEqual(self.priority(scarce, broad, not_belonging=[scarce]), broad)

    def test_excluded_course_is_not_treated_as_named(self):
        excluding = self.rule("Excludes it", 1, q=~Q(full_code=self.FULL_CODE))
        broad = self.rule("Broad", 1000)
        self.assertEqual(self.priority(excluding, broad, not_belonging=[excluding]), broad)

    def test_skips_rule_refusing_transfer_credit(self):
        barred = self.rule("No transfer", 1, transfer_credit_allowed=False)
        broad = self.rule("Broad", 1000)
        self.assertEqual(self.priority(barred, broad, is_transfer=True), broad)

    def test_no_applicable_rule(self):
        self.assertIsNone(self.priority(self.rule("Nope", 1), not_belonging=Rule.objects.all()))


class AssignExcludedCourseTest(TestCase):
    def test_rule_excluding_a_course_is_not_selected_or_offered(self):
        excluding = rule("Excludes it", ~Q(full_code="WRIT-0150"))

        selected, unselected = assign_individual_rule(
            "WRIT-0150",
            None,
            {excluding},
            set(),
            {excluding: "degree"},
            {},
            {(excluding.id, "WRIT-0150"): False},
        )

        self.assertEqual(selected, set())
        self.assertEqual(unselected, set())
