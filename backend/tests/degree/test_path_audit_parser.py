from decimal import Decimal
from os import path

from django.db.models import Q
from django.test import TestCase

from degree.models import Degree
from degree.utils.parse_path_audit import (
    ANY_BLOCK,
    ShareTarget,
    parse_audit,
    parse_term,
    parse_terms,
)


FIXTURES = path.join(path.dirname(path.abspath(__file__)), "fixtures")


def load_audit(name):
    with open(path.join(FIXTURES, name)) as f:
        return f.read()


def blocks_by_value(parsed):
    return {block.req_value: block for block in parsed.blocks}


class ParseAuditTest(TestCase):
    """
    The parser's contract, against real audits trimmed to the blocks under test.
    """

    def setUp(self):
        self.cmpe = Degree(program="EU_BSE", degree="BSE", major="CMPE", concentration=None)
        self.biol = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)

    def test_blocks_and_their_credits(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        blocks = blocks_by_value(parsed)

        self.assertEqual(set(blocks), {"BSE", "CMPE", "U-SEAS-SSH"})
        self.assertEqual(blocks["BSE"].req_type, "DEGREE")
        self.assertEqual(blocks["CMPE"].req_type, "MAJOR")

        # the degree's total comes from the DEGREE block, not a string match on a label
        self.assertEqual(parsed.degree_credits, Decimal("37"))
        self.assertEqual(blocks["CMPE"].credits, Decimal("29"))

        # a term is not a catalog year: srcdb 202630 serves the 2027 catalog
        self.assertEqual(parsed.catalog_year, 2027)

    def test_every_rule_carries_its_block_and_a_count(self):
        # Rule.evaluate asserts a leaf has one or the other, and double counting is resolved
        # from the block a rule belongs to.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        for rule in parsed.rules:
            self.assertTrue(rule.block_type and rule.block_value, rule.title)
            if rule.q:
                self.assertTrue(
                    rule.num is not None or rule.credits is not None,
                    f"{rule.title} has a query but no count",
                )

    def test_share_targets(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        blocks = blocks_by_value(parsed)

        self.assertEqual(
            blocks["CMPE"].share_targets,
            [ShareTarget("MAJOR"), ShareTarget("MINOR"), ShareTarget("CONC")],
        )
        # a block may also name one specific block, or specific majors
        electives = blocks["U-SEAS-SSH"].share_targets
        self.assertIn(ShareTarget("OTHER", "U-SEAS-WREE"), electives)
        self.assertIn(ShareTarget("MAJOR", "AFRC"), electives)

    def test_rule_level_targets_reach_every_rule_beneath_them(self):
        # ShareWith can sit on an individual rule as well as on a block header, and applies to
        # everything underneath it.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        sharing = [
            rule
            for rule in parsed.rules
            if {"kind": "THISBLOCK", "value": None} in rule.share_targets
        ]
        self.assertTrue(sharing)
        self.assertEqual({rule.block_value for rule in sharing}, {"U-SEAS-SSH"})

        # and a rule still inherits its block's own targets
        rule = next(r for r in parsed.rules if r.title == "Prog Lang & Tech I")
        self.assertIn({"kind": "MAJOR", "value": None}, rule.share_targets)

    def test_except_nodes_become_exclusions(self):
        # "may not be satisfied with CIS 2610, CIS 3333, ..." is real data in the XML that the
        # JSON audit does not expose, so parse_degreeworks drops it.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        rule = next(r for r in parsed.rules if r.title == "CIS 1100 or CIS Elective")
        self.assertIn("NOT", rule.q)
        self.assertIn("CIS-2610", rule.q)
        self.assertIn("CIS-1100", rule.q)

    def test_dwattr_is_an_attribute_restriction(self):
        # parse_degreeworks ignores DWATTR, which widens the rule to every course in the
        # department.
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        rules = [r for r in parsed.rules if r.q and "attributes__code__in" in r.q]
        self.assertTrue(any("ABB2" in rule.q for rule in rules))


class OverlayRequirementTest(TestCase):
    """
    MINCLASS and MINCREDIT header qualifiers constrain the courses already applied rather than
    competing for them, so they are parsed as leaf rules that share with what they range over.
    Missing them entirely left a CSCI degree with no area list requirement.
    """

    def test_area_lists_come_from_minclass(self):
        csci = Degree(program="EU_BSE", degree="BSE", major="CSCI", concentration="NCON")
        parsed = parse_audit(load_audit("CSCI-BSE-NCON.xml"), csci)

        area_lists = [r for r in parsed.rules if r.title.startswith("Area List - ")]
        self.assertEqual(5, len(area_lists))
        for rule in area_lists:
            self.assertEqual(rule.num, 1)
            # an overlay on a major ranges over that block
            self.assertIn({"kind": "THISBLOCK", "value": None}, rule.share_targets)

        # "NETS 1500, 2120, CIS 4510" -- the discipline carries forward across commas
        networking = next(r for r in area_lists if r.title.endswith("Networking"))
        for full_code in ["NETS-1500", "NETS-2120", "CIS-4510"]:
            self.assertIn(full_code, networking.q)

        # an ordinary requirement is not an overlay
        prog_lang = next(r for r in parsed.rules if r.title == "Prog Lang & Tech I")
        self.assertNotIn({"kind": "THISBLOCK", "value": None}, prog_lang.share_targets)

    def test_a_degree_level_overlay_ranges_over_the_whole_degree(self):
        # A DEGREE block has no course rules of its own, so THISBLOCK would share with nothing
        # and a course counted toward the major would never advance this requirement.
        biol = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)
        parsed = parse_audit(load_audit("BIOL-BA.xml"), biol)

        rule = next(r for r in parsed.rules if r.title == "Arts and Sciences 31 CU Requirement")
        self.assertEqual(rule.credits, 31)
        self.assertEqual(rule.block_type, "DEGREE")
        self.assertIn("department__code__in", rule.q)
        self.assertEqual(rule.share_targets, [{"kind": ANY_BLOCK, "value": None}])

    def test_a_standalone_block_shares_with_everything(self):
        # The College's Foundations block carries no ShareWith, but is marked STANDALONEBLOCK:
        # DegreeWorks evaluates it outside the degree's shared pool of courses.
        biol = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)
        parsed = parse_audit(load_audit("BIOL-BA.xml"), biol)

        foundations = [r for r in parsed.rules if r.block_value == "U-GE-FND"]
        self.assertTrue(foundations)
        for rule in foundations:
            self.assertIn({"kind": ANY_BLOCK, "value": None}, rule.share_targets)


class SecondMajorTest(TestCase):
    """
    The "College 2nd Major ONLY" programs have a DEGREE block with no credit total, because
    that comes from the student's primary degree. Rejecting them lost exactly the programs a
    dual-major student adds.
    """

    def setUp(self):
        self.csci_ba = Degree(program="AU_BA", degree="BA", major="CSCI", concentration=None)

    def test_parsed_despite_having_no_degree_credit_total(self):
        parsed = parse_audit(load_audit("CSCI-BA.xml"), self.csci_ba)
        self.assertIsNotNone(parsed)
        self.assertIsNone(parsed.degree_credits)
        self.assertEqual(blocks_by_value(parsed)["CSCI"].credits, Decimal("12"))

    def test_an_audit_with_nothing_to_fulfill_is_still_rejected(self):
        empty = """<?xml version="1.0"?><Report><Audit>
            <DegreeData><Block Req_type="DEGREE" Req_value="BA" Cat_yr_start="2027"
                               Title="Degree in Bachelor of Arts"><Header/></Block>
            </DegreeData></Audit></Report>"""
        self.assertIsNone(parse_audit(empty, self.csci_ba))


class TermRestrictionTest(TestCase):
    """
    A DWTERM restriction names one or more terms. Several at once is normal: the COVID
    pass/fail carve-outs list four, which used to abort a whole run.
    """

    def test_term_values(self):
        self.assertEqual(parse_term("Spring 2020"), "2020A")
        self.assertEqual(parse_term("Fall 2020"), "2020C")
        self.assertEqual(parse_term("202010"), "2020A")  # a Path term code means the same
        self.assertEqual(parse_term("2022A"), "2022A")
        self.assertIsNone(parse_term("sometime next year"))

    def test_several_terms_and_operators(self):
        covid = ["Spring 2020", "Summer 2020", "Fall 2020", "Spring 2021"]
        expected = ["2020A", "2020B", "2020C", "2021A"]

        self.assertEqual(parse_terms(covid, "="), Q(semester__in=expected))
        self.assertEqual(parse_terms(covid, None), Q(semester__in=expected))
        self.assertEqual(parse_terms(covid, "<>"), ~Q(semester__in=expected))
        self.assertEqual(parse_terms(covid, "<"), Q(semester__lt="2020A"))
        self.assertEqual(parse_terms(covid, ">"), Q(semester__gt="2021A"))

    def test_an_unusable_restriction_is_ignored_rather_than_narrowing(self):
        # Silently excluding every course would be worse than ignoring the restriction.
        self.assertEqual(parse_terms(["not a term"], "="), Q())
        self.assertEqual(parse_terms(["Spring 2020"], "~="), Q())
