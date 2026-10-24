from decimal import Decimal

from django.db.models import Q
from django.test import TestCase

from degree.models import Degree, Rule
from degree.utils.double_counts import (
    coordinated_degree_pairs,
    get_degree_trees,
    resolve_double_counts,
)
from degree.utils.mt_degrees import (
    mt_data,
    mt_seas_audit,
    mt_undeclared_degree,
    mt_variant,
    mt_wharton_audit,
)
from degree.utils.parse_path_audit import parse_audit
from tests.degree.test_path_audit_parser import blocks_by_value, load_audit


# The shape of the IfStmt SEAS uses to switch an M&T student's General Electives, reduced to
# the condition under test.
NUMMAJORS_AUDIT = """<?xml version="1.0" encoding="UTF-8"?>
<Report>
  <Audit>
    <Block Cat_yr_start="2025" Req_type="OTHER" Req_value="U-SEAS-SSH" Title="General Electives">
      <Rule Label="IF Statement" RuleType="IfStmt" Rule_id="1-0">
        <BooleanEvaluation>False</BooleanEvaluation>
        <Requirement>
          <LeftCondition>
            <Rop Evaluation="0" Left="NUMMAJORS" Operator="&gt;=" Right="2"/>
          </LeftCondition>
          <IfPart>
            <Rule Label="Technology in Business and Society" RuleType="Course" Rule_id="1-0-0">
              <Requirement Credits_begin="2"><Course Disc="WH" Num="1010"/></Requirement>
            </Rule>
          </IfPart>
          <ElsePart>
            <Rule Label="Social Science" RuleType="Course" Rule_id="1-0-1">
              <Requirement Credits_begin="2"><Course Disc="ECON" Num="0100"/></Requirement>
            </Rule>
          </ElsePart>
        </Requirement>
      </Rule>
    </Block>
  </Audit>
</Report>
"""


def leaf_titles(parsed, block_value=None):
    return {
        rule.title
        for rule in parsed.rules
        if rule.q and (block_value is None or rule.block_value == block_value)
    }


class MTWhartonAuditTest(TestCase):
    """
    The Wharton side of M&T: a public Wharton audit with its OTHER blocks replaced by the M&T
    ones from degree/data/mt_wharton_blocks.json.
    """

    def setUp(self):
        self.audit = load_audit("FNCS-BS-2026.xml")
        self.plain = Degree(program="WU_BS", degree="BS", major="FNCS", concentration=None)
        self.as_plain = parse_audit(self.audit, self.plain)

    def mt_audit(self, degree, keep_major=True):
        return mt_wharton_audit(parse_audit(self.audit, degree), self.as_plain, keep_major)

    def test_replaces_the_wharton_blocks_and_keeps_the_concentration(self):
        parsed = self.mt_audit(mt_variant(self.plain))
        blocks = blocks_by_value(parsed)

        self.assertEqual(
            set(blocks), {"BS", "FNCS", "U-WQCS", "U-WBUS", "U-WLAS", "U-WBBR2", "U-MT"}
        )
        self.assertEqual(blocks["U-WQCS"].credits, Decimal("4"))
        self.assertEqual(blocks["U-WBUS"].credits, Decimal("11.5"))
        self.assertEqual(blocks["U-WLAS"].credits, Decimal("5"))
        self.assertEqual(blocks["U-WBBR2"].credits, Decimal("2"))
        self.assertEqual(blocks["U-MT"].credits, Decimal("1.5"))

        # the concentration is the public one, unchanged
        self.assertEqual(leaf_titles(parsed, "FNCS"), leaf_titles(self.as_plain, "FNCS"))

    def test_two_degrees_share_one_total(self):
        self.assertEqual(self.as_plain.degree_credits, Decimal("37"))
        self.assertEqual(self.mt_audit(mt_variant(self.plain)).degree_credits, Decimal("46"))

    def test_rules_shared_with_plain_wharton_come_from_its_audit(self):
        parsed = self.mt_audit(mt_variant(self.plain))
        for title in ["Critical Writing Seminar", "Foreign Language Proficiency"]:
            [mt_rule] = [r for r in parsed.rules if r.title == title]
            [plain_rule] = [r for r in self.as_plain.rules if r.q and r.title == title]
            self.assertEqual(mt_rule.q, plain_rule.q)
            self.assertEqual(mt_rule.block_value, "U-WLAS")

    def test_every_leaf_carries_its_block_and_a_count(self):
        parsed = self.mt_audit(mt_variant(self.plain))
        for rule in parsed.rules:
            self.assertTrue(rule.block_type and rule.block_value, rule.title)
            if rule.q:
                self.assertTrue(rule.num is not None or rule.credits is not None, rule.title)

    def test_breadth_may_share_with_the_mt_block(self):
        parsed = self.mt_audit(mt_variant(self.plain))
        [breadth] = [r for r in parsed.rules if r.q and r.block_value == "U-WBBR2"]
        self.assertIn({"kind": "OTHER", "value": "U-MT"}, breadth.share_targets)

    def test_undeclared_student_has_no_concentration(self):
        parsed = self.mt_audit(mt_undeclared_degree(), keep_major=False)
        self.assertNotIn("FNCS", blocks_by_value(parsed))
        self.assertIn("U-MT", blocks_by_value(parsed))
        self.assertEqual(parsed.degree_credits, Decimal("46"))


class MTProgramsTest(TestCase):
    def test_variants(self):
        def variant(program):
            v = mt_variant(Degree(program=program, degree="X", major="M"))
            return v and v.program

        self.assertEqual(variant("EU_BSE"), "EU_BSE_MANT")
        self.assertEqual(variant("EU_BAS"), "EU_BAS_MANT")
        self.assertEqual(variant("WU_BS"), "WU_BS_MANT")
        self.assertIsNone(variant("AU_BA"))
        self.assertIsNone(variant("EM_MSE"))

    def test_data_file_rules_are_well_formed(self):
        def leaves(rules):
            for rule in rules:
                if "rules" in rule:
                    yield from leaves(rule["rules"])
                else:
                    yield rule

        for block in mt_data()["blocks"]:
            for rule in leaves(block["rules"]):
                if "from_public" in rule:
                    continue
                self.assertTrue("num" in rule or "credits" in rule, rule["title"])
                self.assertTrue(
                    rule.get("courses") or rule.get("attributes") or rule.get("departments"),
                    rule["title"],
                )
                for code in rule.get("courses", []):
                    self.assertRegex(code, r"^[A-Z]{2,4}-\d{4}$")


class MTSeasAuditTest(TestCase):
    def test_an_mt_student_has_two_majors(self):
        plain = Degree(program="EU_BSE", degree="BSE", major="CSCI")
        as_plain = parse_audit(NUMMAJORS_AUDIT, plain)
        as_mt = mt_seas_audit(parse_audit(NUMMAJORS_AUDIT, mt_variant(plain)))

        # outside M&T the count is unknown, so the audit's own evaluation stands
        self.assertEqual(leaf_titles(as_plain), {"Social Science"})
        self.assertEqual(leaf_titles(as_mt), {"Technology in Business and Society"})
        self.assertEqual(as_mt.degree_credits, Decimal("46"))


class MTDoubleCountTest(TestCase):
    """The two halves of an M&T dual degree may count a course toward both."""

    def make_degree(self, program, degree, block_value):
        d = Degree.objects.create(program=program, degree=degree, major="X", year=2026)
        root = Rule.objects.create(title=block_value, block_type="OTHER", block_value=block_value)
        leaf = Rule.objects.create(
            title=f"{block_value} leaf",
            parent=root,
            q=repr(Q(full_code="EAS-2030")),
            num=1,
            block_type="OTHER",
            block_value=block_value,
            share_targets=[],
        )
        d.rules.add(root)
        return d, leaf

    def test_mt_halves_share_and_plain_degrees_do_not(self):
        wharton, wharton_rule = self.make_degree("WU_BS_MANT", "BS", "U-WBUS")
        seas, seas_rule = self.make_degree("EU_BSE_MANT", "BSE", "U-SEAS-SSH")
        double_counts = resolve_double_counts(get_degree_trees([wharton, seas]))
        self.assertIn(seas_rule, double_counts.get(wharton_rule, set()))
        self.assertIn(wharton_rule, double_counts.get(seas_rule, set()))

        plain_wharton, plain_wharton_rule = self.make_degree("WU_BS", "BS", "U-WLAS")
        plain_seas, plain_seas_rule = self.make_degree("EU_BSE", "BSE", "U-SEAS-WREE")
        double_counts = resolve_double_counts(get_degree_trees([plain_wharton, plain_seas]))
        self.assertNotIn(plain_seas_rule, double_counts.get(plain_wharton_rule, set()))

    def test_pairs_need_one_wharton_and_one_seas_half(self):
        wharton, _ = self.make_degree("WU_BS_MANT", "BS", "U-WBUS")
        seas, _ = self.make_degree("EU_BSE_MANT", "BSE", "U-SEAS-SSH")
        plain, _ = self.make_degree("AU_BA", "BA", "U-GE")
        self.assertEqual(coordinated_degree_pairs([wharton, seas, plain]), [(wharton, seas)])
