from os import path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase

from degree.models import Degree, DegreePlan, Fulfillment, Major, Minor, Rule
from degree.utils.parse_path_audit import move_course_assignments, parse_audit, save_parsed_audit
from degree.utils.path_client import PathError


FIXTURES = path.join(path.dirname(path.abspath(__file__)), "fixtures")
COMMAND = "degree.management.commands.fetch_degrees_from_path"


def load_audit(name):
    with open(path.join(FIXTURES, name)) as f:
        return f.read()


def fetch(audit_xml=None):
    info = {
        "sis_prog_code": "AU_BA",
        "degc_code": "BA",
        "majr_code": "BIOL",
        "conc_code": None,
        "prog_name": "Biology, BA",
        "audit_xml": audit_xml or load_audit("BIOL-BA.xml"),
    }
    with patch(f"{COMMAND}.PathClient") as client:
        client.return_value.program_info.return_value = info
        call_command("fetch_degrees_from_path", srcdb=["202630"], program=["BIOL-BA"], verbosity=0)


class ReparsingTest(TestCase):
    def setUp(self):
        fetch()
        self.degree = Degree.objects.get(major="BIOL")
        self.major = Major.objects.get(program_code="BIOL-BA")
        person = get_user_model().objects.create_user(username="t", password="x")
        self.plan = DegreePlan.objects.create(name="Biology", person=person)
        self.plan.degrees.add(self.degree)
        self.plan.majors.add(self.major)

        self.credit_rule = Rule.objects.get(title="Arts and Sciences 31 CU Requirement")
        self.fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CHEM-1012", semester="2023C"
        )
        self.fulfillment.rules.add(self.credit_rule)

    def test_refetching_changes_nothing(self):
        before = set(Rule.objects.values_list("id", "q"))
        fetch()

        self.assertEqual(set(Rule.objects.values_list("id", "q")), before)
        self.assertEqual(Degree.objects.get(major="BIOL").pk, self.degree.pk)
        self.assertEqual(Major.objects.get(program_code="BIOL-BA").pk, self.major.pk)
        self.assertEqual(list(self.plan.degrees.all()), [self.degree])
        self.assertEqual(list(self.plan.majors.all()), [self.major])
        self.assertEqual(list(self.fulfillment.rules.all()), [self.credit_rule])

    def test_a_degree_and_its_major_keep_sharing_rules(self):
        fetch()
        major_rules = set(self.major.rules.values_list("id", flat=True))
        self.assertTrue(major_rules)
        self.assertLessEqual(major_rules, set(self.degree.rules.values_list("id", flat=True)))

    def test_a_changed_rule_is_patched_in_place(self):
        Rule.objects.filter(pk=self.credit_rule.pk).update(q=repr(Q(department__code__in=["X"])))
        fetch()

        self.credit_rule.refresh_from_db()
        self.assertIn("AU16", self.credit_rule.q)
        self.assertEqual(list(self.fulfillment.rules.all()), [self.credit_rule])

    def test_nothing_to_move_costs_no_queries(self):
        with self.assertNumQueries(0):
            move_course_assignments([], self.degree)

    def test_a_rule_with_a_new_title_replaces_the_old_one(self):
        with self.assertLogs("degree.utils.parse_path_audit", "WARNING") as logs:
            fetch(load_audit("BIOL-BA.xml").replace("31 CU Requirement", "32 CU Requirement"))
        self.assertIn("unassigned 1 course(s)", logs.output[0])

        self.assertFalse(Rule.objects.filter(pk=self.credit_rule.pk).exists())
        self.assertTrue(Rule.objects.filter(title="Arts and Sciences 32 CU Requirement").exists())
        self.assertEqual(list(self.fulfillment.rules.all()), [])
        self.assertTrue(Fulfillment.objects.filter(pk=self.fulfillment.pk).exists())

    def test_identical_siblings_are_not_shuffled(self):
        before = dict(Rule.objects.values_list("id", "q"))
        fetch()
        self.assertEqual(dict(Rule.objects.values_list("id", "q")), before)


class DeduplicatedRulesTest(TestCase):
    def setUp(self):
        fetch()
        self.degree = Degree.objects.get(major="BIOL")
        self.root = self.degree.rules.get(block_type="DEGREE")
        self.credit_rule = Rule.objects.get(title="Arts and Sciences 31 CU Requirement")

        self.other = Degree.objects.create(
            program="AU_BA", degree="BA", major="CHEM", concentration=None, year=2027
        )
        self.other.rules.add(self.root)

        person = get_user_model().objects.create_user(username="t", password="x")
        self.plan = DegreePlan.objects.create(name="Biology", person=person)
        self.plan.degrees.add(self.degree)
        self.fulfillment = Fulfillment.objects.create(
            degree_plan=self.plan, full_code="CHEM-1012", semester="2023C"
        )
        self.fulfillment.rules.add(self.credit_rule)

    def test_patching_a_shared_rule_leaves_the_other_degree_alone(self):
        old_q = self.credit_rule.q
        fetch(load_audit("BIOL-BA.xml").replace("YDSH @, ", ""))

        self.credit_rule.refresh_from_db()
        self.assertEqual(self.credit_rule.q, old_q)
        self.assertIn(self.root, self.other.rules.all())
        self.assertNotIn(self.root, self.degree.rules.all())

    def test_courses_follow_the_degree_to_its_own_copy(self):
        fetch(load_audit("BIOL-BA.xml").replace("YDSH @, ", ""))

        new_rule = self.fulfillment.rules.get()
        self.assertNotEqual(new_rule.pk, self.credit_rule.pk)
        self.assertEqual(new_rule.title, self.credit_rule.title)
        self.assertNotIn("YDSH", new_rule.q)

    def test_a_plan_on_both_degrees_keeps_the_shared_rule_too(self):
        self.plan.degrees.add(self.other)
        fetch(load_audit("BIOL-BA.xml").replace("YDSH @, ", ""))

        self.assertEqual(self.fulfillment.rules.count(), 2)
        self.assertIn(self.credit_rule, self.fulfillment.rules.all())


class TermOrderTest(TestCase):

    NEW_TERM, OLD_TERM = "202630", "202610"
    NEW_TITLE = "Arts and Sciences 31 CU Requirement"
    OLD_TITLE = "Arts and Sciences 30 CU Requirement"

    def info(self, audit_xml):
        return {
            "sis_prog_code": "AU_BA",
            "degc_code": "BA",
            "majr_code": "BIOL",
            "conc_code": None,
            "prog_name": "Biology, BA",
            "audit_xml": audit_xml,
        }

    def fetch_terms(self, by_term, srcdb=None):
        def program_info(code, srcdb):
            result = by_term[srcdb]
            if isinstance(result, Exception):
                raise result
            return self.info(result)

        with patch(f"{COMMAND}.PathClient") as client:
            client.return_value.program_info.side_effect = program_info
            call_command(
                "fetch_degrees_from_path",
                srcdb=srcdb or [self.OLD_TERM, self.NEW_TERM],
                program=["BIOL-BA"],
                verbosity=0,
            )

    def older_version(self):
        return load_audit("BIOL-BA.xml").replace("31 CU Requirement", "30 CU Requirement")

    def test_the_newest_term_wins_a_catalog_year_in_any_argument_order(self):
        self.fetch_terms(
            {self.NEW_TERM: load_audit("BIOL-BA.xml"), self.OLD_TERM: self.older_version()}
        )

        self.assertTrue(Rule.objects.filter(title=self.NEW_TITLE).exists())
        self.assertFalse(Rule.objects.filter(title=self.OLD_TITLE).exists())

    def test_an_older_term_still_saves_its_own_catalog_year(self):
        older_year = load_audit("BIOL-BA.xml").replace('Cat_yr_start="2027"', 'Cat_yr_start="2026"')
        self.fetch_terms({self.NEW_TERM: load_audit("BIOL-BA.xml"), self.OLD_TERM: older_year})

        self.assertEqual(
            set(Degree.objects.filter(major="BIOL").values_list("year", flat=True)), {2026, 2027}
        )

    def test_a_failed_fetch_keeps_older_terms_from_writing_the_program(self):
        self.fetch_terms({self.NEW_TERM: load_audit("BIOL-BA.xml")}, srcdb=[self.NEW_TERM])

        self.fetch_terms(
            {self.NEW_TERM: ConnectionError("down"), self.OLD_TERM: self.older_version()}
        )

        self.assertTrue(Rule.objects.filter(title=self.NEW_TITLE).exists())
        self.assertFalse(Rule.objects.filter(title=self.OLD_TITLE).exists())

    def test_a_term_without_the_program_does_not_block_older_terms(self):
        self.fetch_terms(
            {self.NEW_TERM: PathError("No audit_xml"), self.OLD_TERM: self.older_version()}
        )

        self.assertTrue(Rule.objects.filter(title=self.OLD_TITLE).exists())


class DirectSaveTest(TestCase):
    def test_saving_twice_without_a_major_keeps_the_rows(self):
        def save():
            degree = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)
            parsed = parse_audit(load_audit("BIOL-BA.xml"), degree)
            degree.year = parsed.catalog_year
            save_parsed_audit(parsed, degree)
            return degree

        first, count = save(), Rule.objects.count()
        second = save()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Rule.objects.count(), count)
        self.assertEqual(Minor.objects.count(), 0)
