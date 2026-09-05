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
    Parses real Path@Penn audits saved from courses.upenn.edu. The fixtures cover Engineering
    (at two catalog years), the College and Wharton, which differ in how many blocks they have
    and in how much of the share policy they publish.
    """

    def setUp(self):
        self.cmpe = Degree(program="EU_BSE", degree="BSE", major="CMPE", concentration=None)
        self.biol = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)
        self.fncs = Degree(program="WU_BS", degree="BS", major="FNCS", concentration=None)

    def test_degree_credits_come_from_the_degree_block(self):
        for fixture, degree, credits in [
            ("CMPE-BSE-2026.xml", self.cmpe, Decimal("37")),
            ("CMPE-BSE-2021.xml", self.cmpe, Decimal("37")),
            ("BIOL-BA.xml", self.biol, Decimal("36")),
            ("FNCS-BS.xml", self.fncs, Decimal("37")),
        ]:
            parsed = parse_audit(load_audit(fixture), degree)
            self.assertIsNotNone(parsed, fixture)
            self.assertEqual(parsed.degree_credits, credits, fixture)

    def test_catalog_year_read_from_the_audit(self):
        # A term is not a catalog year: srcdb 202630 serves the 2027 catalog.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        self.assertEqual(parsed.catalog_year, 2027)

        parsed = parse_audit(load_audit("CMPE-BSE-2021.xml"), self.cmpe)
        self.assertEqual(parsed.catalog_year, 2021)

    def test_blocks(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        blocks = blocks_by_value(parsed)
        self.assertEqual(set(blocks), {"BSE", "CMPE", "U-SEAS-SSH"})
        self.assertEqual(blocks["BSE"].req_type, "DEGREE")
        self.assertEqual(blocks["CMPE"].req_type, "MAJOR")
        self.assertEqual(blocks["CMPE"].credits, Decimal("29"))

    def test_blocks_without_a_credit_requirement(self):
        # The College's General Education blocks impose no credit total of their own.
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        blocks = blocks_by_value(parsed)
        self.assertIsNone(blocks["U-GE-FND"].credits)
        self.assertIsNone(blocks["U-GE-SCTR"].credits)
        self.assertEqual(blocks["BIOL"].credits, Decimal("17"))

    def test_degree_block_kept_even_though_it_has_no_rules(self):
        # A DEGREE block is usually just pointers to the other blocks, but it carries the
        # credit requirement, so it must survive parsing.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        degree_block = blocks_by_value(parsed)["BSE"]
        self.assertEqual(degree_block.req_type, "DEGREE")
        self.assertIsNone(degree_block.root_rule)
        self.assertEqual(degree_block.credits, Decimal("37"))

    def test_share_targets(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        blocks = blocks_by_value(parsed)

        self.assertEqual(
            blocks["CMPE"].share_targets,
            [ShareTarget("MAJOR"), ShareTarget("MINOR"), ShareTarget("CONC")],
        )

        # The General Electives block names another block, then a long list of majors.
        electives = blocks["U-SEAS-SSH"].share_targets
        self.assertIn(ShareTarget("OTHER", "U-SEAS-WREE"), electives)
        self.assertIn(ShareTarget("MAJOR", "AFRC"), electives)
        self.assertIn(ShareTarget("MAJOR", "LAWS"), electives)
        self.assertIn(ShareTarget("CONC"), electives)

    def test_wharton_publishes_share_policy_we_never_encoded(self):
        # double_counts.DOUBLE_COUNT_ENTRIES has no Wharton entries at all.
        parsed = parse_audit(load_audit("FNCS-BS.xml"), self.fncs)
        blocks = blocks_by_value(parsed)
        self.assertIn(ShareTarget("OTHER", "U-SCHOLARS"), blocks["U-WFYF"].share_targets)
        self.assertIn(ShareTarget("MINOR"), blocks["U-WBUS"].share_targets)
        self.assertIn(ShareTarget("OTHER", "U-MT"), blocks["U-WBBR2"].share_targets)

    def test_rule_level_share_policy(self):
        # ShareWith can sit on an individual rule as well as on a block header.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        sharing = [
            rule
            for rule in parsed.rules
            if {"kind": "THISBLOCK", "value": None} in rule.share_targets
        ]
        self.assertTrue(sharing)
        self.assertEqual({rule.block_value for rule in sharing}, {"U-SEAS-SSH"})

    def test_every_leaf_rule_has_a_count(self):
        # Rule.evaluate asserts on this.
        for fixture, degree in [
            ("CMPE-BSE-2026.xml", self.cmpe),
            ("CMPE-BSE-2021.xml", self.cmpe),
            ("BIOL-BA.xml", self.biol),
            ("FNCS-BS.xml", self.fncs),
        ]:
            parsed = parse_audit(load_audit(fixture), degree)
            for rule in parsed.rules:
                if rule.q:
                    self.assertTrue(
                        rule.num is not None or rule.credits is not None,
                        f"{fixture}: {rule.title} has a query but no count",
                    )

    def test_except_nodes_become_exclusions(self):
        # "Note: This requirement may not be satisfied with CIS 2610, CIS 3333, ..." is real
        # data in the XML. parse_degreeworks drops it, because the JSON audit does not expose
        # it at all.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        rule = next(r for r in parsed.rules if r.title == "CIS 1100 or CIS Elective")
        self.assertIn("NOT", rule.q)
        self.assertIn("CIS-2610", rule.q)
        self.assertIn("CIS-1100", rule.q)

    def test_course_number_ranges(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        rule = next(r for r in parsed.rules if r.title == "Advanced CIS or ESE Electives")
        self.assertIn("code__gte", rule.q)
        self.assertIn("3000", rule.q)
        self.assertEqual(rule.credits, 2)

    def test_attribute_restrictions(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        rule = next(r for r in parsed.rules if r.title == "Math or Natural Science Elective")
        self.assertIn("attributes__code__in", rule.q)
        self.assertIn("EUMA", rule.q)

    def test_dwattr_treated_as_an_attribute_restriction(self):
        # parse_degreeworks ignores DWATTR, which widens the rule to every BIOL course.
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        rules = [r for r in parsed.rules if r.q and "attributes__code__in" in r.q]
        self.assertTrue(any("ABB2" in rule.q for rule in rules))


class SecondMajorTest(TestCase):
    """
    The "College 2nd Major ONLY" programs -- 14 of the 279 undergraduate ones -- have a DEGREE
    block with no credit total, because that comes from the student's primary degree. They
    must still be stored: they are exactly what a dual-major student adds to a plan.
    """

    def setUp(self):
        self.csci_ba = Degree(program="AU_BA", degree="BA", major="CSCI", concentration=None)

    def test_parsed_despite_having_no_degree_credit_total(self):
        parsed = parse_audit(load_audit("CSCI-BA.xml"), self.csci_ba)
        self.assertIsNotNone(parsed)
        self.assertIsNone(parsed.degree_credits)
        self.assertEqual(parsed.catalog_year, 2027)

    def test_the_major_block_is_intact(self):
        parsed = parse_audit(load_audit("CSCI-BA.xml"), self.csci_ba)
        major = blocks_by_value(parsed)["CSCI"]
        self.assertEqual(major.req_type, "MAJOR")
        self.assertEqual(major.credits, Decimal("12"))
        self.assertTrue(major.share_targets)
        self.assertTrue([r for r in parsed.rules if r.block_value == "CSCI" and r.q])

    def test_an_audit_with_nothing_to_fulfill_is_still_rejected(self):
        # Dropping the credit-total requirement must not turn every unparseable audit into a
        # degree with no rules.
        empty = """<?xml version="1.0"?><Report><Audit>
            <DegreeData><Block Req_type="DEGREE" Req_value="BA" Cat_yr_start="2027"
                               Title="Degree in Bachelor of Arts"><Header/></Block>
            </DegreeData></Audit></Report>"""
        self.assertIsNone(parse_audit(empty, self.csci_ba))


class ShareTargetsOnRulesTest(TestCase):
    """
    The share policy is denormalized onto each rule, so a rule alone carries everything
    `double_counts.resolve_double_counts` needs.
    """

    def setUp(self):
        self.cmpe = Degree(program="EU_BSE", degree="BSE", major="CMPE", concentration=None)
        self.biol = Degree(program="AU_BA", degree="BA", major="BIOL", concentration=None)

    def test_block_identity_on_every_rule(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        major_rules = [r for r in parsed.rules if r.block_value == "CMPE"]
        self.assertTrue(major_rules)
        for rule in major_rules:
            self.assertEqual(rule.block_type, "MAJOR")

        electives = [r for r in parsed.rules if r.block_value == "U-SEAS-SSH"]
        self.assertTrue(electives)
        for rule in electives:
            self.assertEqual(rule.block_type, "OTHER")

    def test_block_share_targets_reach_the_leaves(self):
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        rule = next(r for r in parsed.rules if r.title == "Prog Lang & Tech I")
        self.assertIn({"kind": "MAJOR", "value": None}, rule.share_targets)
        self.assertIn({"kind": "MINOR", "value": None}, rule.share_targets)
        self.assertIn({"kind": "CONC", "value": None}, rule.share_targets)

    def test_rule_level_targets_are_inherited_by_descendants(self):
        # A ShareWith on a Subset or Group applies to everything underneath it.
        parsed = parse_audit(load_audit("CMPE-BSE-2026.xml"), self.cmpe)
        inheriting = [
            r for r in parsed.rules if {"kind": "THISBLOCK", "value": None} in r.share_targets
        ]
        self.assertTrue(inheriting)
        for rule in inheriting:
            self.assertEqual(rule.block_type, "OTHER")

    def test_computer_science_area_lists_are_overlays_on_the_major(self):
        # CSCI's area lists are MINCLASS header qualifiers, not rules: they constrain the
        # courses already applied to the major rather than competing for them. So they are
        # parsed as leaf rules that share with the rest of their block, which is what makes a
        # course counted toward "CIS Elective" also satisfy the Networking area list.
        csci = Degree(program="EU_BSE", degree="BSE", major="CSCI", concentration="NCON")
        parsed = parse_audit(load_audit("CSCI-BSE-NCON.xml"), csci)

        area_lists = [r for r in parsed.rules if r.title.startswith("Area List - ")]
        self.assertEqual(5, len(area_lists))
        for rule in area_lists:
            self.assertEqual(rule.block_type, "MAJOR")
            self.assertEqual(rule.block_value, "CSCI")
            self.assertEqual(rule.num, 1)
            self.assertIn({"kind": "THISBLOCK", "value": None}, rule.share_targets)

        # The ordinary major requirements are not overlays, so they stay exclusive.
        prog_lang = next(r for r in parsed.rules if r.title == "Prog Lang & Tech I")
        self.assertNotIn({"kind": "THISBLOCK", "value": None}, prog_lang.share_targets)

    def test_area_list_course_shorthand(self):
        # "NETS 1500, 2120, CIS 4510, ..." -- the discipline carries forward across commas.
        csci = Degree(program="EU_BSE", degree="BSE", major="CSCI", concentration="NCON")
        parsed = parse_audit(load_audit("CSCI-BSE-NCON.xml"), csci)
        networking = next(r for r in parsed.rules if r.title == "Area List - Networking")
        for full_code in ["NETS-1500", "NETS-2120", "CIS-4510", "CIS-3310"]:
            self.assertIn(full_code, networking.q)

    def test_college_credit_requirement_from_mincredit(self):
        # "Arts and Sciences 31 CU Requirement" is a MINCREDIT qualifier on the DEGREE block,
        # listing every Arts and Sciences department as "DEPT @".
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        rule = next(r for r in parsed.rules if r.title == "Arts and Sciences 31 CU Requirement")
        self.assertEqual(rule.credits, 31)
        self.assertEqual(rule.block_type, "DEGREE")
        self.assertIn("department__code__in", rule.q)
        self.assertIn("BIOL", rule.q)

        # A DEGREE block has no course rules of its own, so an overlay there ranges over the
        # courses applied anywhere in the degree -- ANYBLOCK, not THISBLOCK. With THISBLOCK it
        # would share with nothing, and a Biology course counted toward the major would never
        # advance the student's Arts and Sciences credit total.
        self.assertEqual(rule.share_targets, [{"kind": ANY_BLOCK, "value": None}])

    def test_concentration_blocks_share_with_the_major(self):
        # Two independent mechanisms say the same thing: the major block names (CONC), and the
        # concentration block is marked STANDALONEBLOCK.
        csci = Degree(program="EU_BSE", degree="BSE", major="CSCI", concentration="ARIN")
        parsed = parse_audit(load_audit("CSCI-BSE-ARIN.xml"), csci)
        blocks = blocks_by_value(parsed)
        self.assertEqual(blocks["ARIN"].req_type, "CONC")
        self.assertIn(ShareTarget(ANY_BLOCK), blocks["ARIN"].share_targets)
        self.assertIn(ShareTarget("CONC"), blocks["CSCI"].share_targets)

    def test_college_foundations_is_a_standalone_block(self):
        # The College's General Education blocks carry no NONEXCLUSIVE qualifier, but
        # Foundations is marked STANDALONEBLOCK: DegreeWorks evaluates it independently of the
        # degree's shared pool, which is how a Foundations course also counts toward the
        # major without any ShareWith saying so.
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        foundations = [r for r in parsed.rules if r.block_value == "U-GE-FND"]
        self.assertTrue(foundations)
        for rule in foundations:
            self.assertIn({"kind": "ANYBLOCK", "value": None}, rule.share_targets)

        major = [r for r in parsed.rules if r.block_value == "BIOL" and r.q]
        self.assertTrue(major)
        for rule in major:
            self.assertIn({"kind": "MAJOR", "value": None}, rule.share_targets)

    def test_sectors_covered_by_the_major_are_dropped_as_already_complete(self):
        # The Sectors block does not share with the major. Instead the sectors a Biology major
        # inevitably covers arrive as Complete rules ("Sector 5: The Living World Fulfilled by
        # Major Course"), which parse_rules drops because nothing remains to be done. The
        # block's own requirement is already net of them: 5 classes, 5 remaining sector rules.
        parsed = parse_audit(load_audit("BIOL-BA.xml"), self.biol)
        sectors = [r for r in parsed.rules if r.block_value == "U-GE-SCTR" and r.q]
        self.assertEqual(5, len(sectors))
        self.assertFalse(any("Fulfilled by Major Course" in rule.title for rule in sectors))


class TermRestrictionTest(TestCase):
    """
    DWTERM restrictions name one or more terms and compare against them with an operator.
    A full-catalog run hit a COVID pass/fail carve-out listing four terms at once.
    """

    def test_term_values(self):
        self.assertEqual(parse_term("Spring 2020"), "2020A")
        self.assertEqual(parse_term("Summer 2020"), "2020B")
        self.assertEqual(parse_term("Fall 2020"), "2020C")
        # Path term codes mean the same thing
        self.assertEqual(parse_term("202010"), "2020A")
        self.assertEqual(parse_term("202030"), "2020C")
        # already one of ours
        self.assertEqual(parse_term("2022A"), "2022A")

    def test_unreadable_term_is_dropped_not_raised(self):
        self.assertIsNone(parse_term("sometime next year"))

    def test_several_terms(self):
        covid = ["Spring 2020", "Summer 2020", "Fall 2020", "Spring 2021"]
        expected = ["2020A", "2020B", "2020C", "2021A"]

        self.assertEqual(parse_terms(covid, "="), Q(semester__in=expected))
        self.assertEqual(parse_terms(covid, "<>"), ~Q(semester__in=expected))
        # no operator behaves like "="
        self.assertEqual(parse_terms(covid, None), Q(semester__in=expected))

    def test_ordered_comparisons_use_the_range(self):
        terms = ["Fall 2020", "Spring 2020"]
        self.assertEqual(parse_terms(terms, "<"), Q(semester__lt="2020A"))
        self.assertEqual(parse_terms(terms, ">"), Q(semester__gt="2020C"))
        self.assertEqual(parse_terms(terms, "<="), Q(semester__lte="2020C"))
        self.assertEqual(parse_terms(terms, ">="), Q(semester__gte="2020A"))

    def test_unusable_restriction_is_ignored_rather_than_narrowing(self):
        # An unreadable restriction must not silently exclude every course.
        self.assertEqual(parse_terms(["not a term"], "="), Q())
        self.assertEqual(parse_terms(["Spring 2020"], "~="), Q())
