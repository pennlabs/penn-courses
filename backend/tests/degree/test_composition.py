from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase

from courses.models import Attribute
from courses.util import get_or_create_course_and_section
from degree.data.dual_programs import load
from degree.models import Degree, DegreePlan, DualProgram, Major, Rule
from degree.utils.composition import compose
from degree.utils.degree_logic import allocate_rules, map_rules_and_degrees, summarize_plan
from degree.utils.double_counts import get_degree_trees, resolve_double_counts

from .test_double_counting import TEST_SEMESTER


def course(full_code, attributes=()):
    course_obj, _, _, _ = get_or_create_course_and_section(f"{full_code}-001", TEST_SEMESTER)
    for code in attributes:
        attribute, _ = Attribute.objects.get_or_create(code=code, defaults={"school": "WH"})
        course_obj.attributes.add(attribute)
    return course_obj


def leaf(title, full_code, block_type, block_value, **kwargs):
    return Rule.objects.create(
        title=title,
        q=repr(Q(full_code=full_code)),
        num=1,
        block_type=block_type,
        block_value=block_value,
        **kwargs,
    )


class CompositionKindTest(TestCase):
    def setUp(self):
        self.person = get_user_model().objects.create_user(username="k", password="x")

    def plan(self, name):
        return DegreePlan.objects.create(name=name, person=self.person)

    def test_one_degree_is_single(self):
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        plan = self.plan("one")
        plan.degrees.add(degree)
        self.assertEqual(compose(plan).kind, "single")
        self.assertFalse(compose(plan).policy.cross_component_sharing)

    def test_two_college_degrees_are_one_college_degree(self):
        econ = Degree.objects.create(
            program="AU_BA",
            degree="BA",
            major="ECON",
            major_name="Economics",
            year=2026,
            credits=36,
        )
        math = Degree.objects.create(
            program="AU_BA",
            degree="BA",
            major="MATH",
            major_name="Mathematics",
            year=2026,
            credits=36,
        )
        writing = Rule.objects.create(
            title="Writing",
            q=repr(Q(full_code="WRIT-0010")),
            num=1,
            block_type="OTHER",
            block_value="U-GE",
        )
        econ_major = leaf("Economics", "ECON-0100", "MAJOR", "ECON")
        math_major = leaf("Mathematics", "MATH-1400", "MAJOR", "MATH")
        econ.rules.add(writing, econ_major)
        math.rules.add(writing, math_major)
        plan = self.plan("college")
        plan.degrees.add(econ, math)

        composition = compose(plan)
        self.assertEqual(composition.kind, "cas_double_major")
        roles = {component.role for component in composition.components}
        self.assertEqual(roles, {"college", "major"})
        college = next(
            component for component in composition.components if component.role == "college"
        )
        self.assertFalse(college.removable)
        self.assertEqual(college.key, f"college:{econ.id}")
        # The second degree's writing requirement is not a second copy.
        self.assertEqual(
            [component.key for component in composition.components if component.role == "college"],
            [f"college:{econ.id}"],
        )

    def test_engineering_and_a_college_major_share_across_components(self):
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="MEAM", year=2026)
        major = Major.objects.create(
            program_code="MATH-BA-GEN", code="MATH", name="Mathematics", year=2026
        )
        plan = self.plan("second")
        plan.degrees.add(degree)
        plan.majors.add(major)
        composition = compose(plan)
        self.assertEqual(composition.kind, "cross_school_dual")
        self.assertTrue(composition.policy.cross_component_sharing)

    def test_submatriculation(self):
        bse = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        mse = Degree.objects.create(program="EM_MSE", degree="MSE", major="CIS", year=2026)
        plan = self.plan("sub")
        plan.degrees.add(bse, mse)
        self.assertEqual(compose(plan).kind, "submatriculation")

    def test_a_specific_major_target_stays_inside_one_degree(self):
        degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        named = Rule.objects.create(
            title="Major",
            q=repr(Q(full_code="CIS-1200")),
            num=1,
            block_type="MAJOR",
            block_value="CIS",
            share_targets=[{"kind": "MAJOR", "value": "PHYS"}],
        )
        sibling = Rule.objects.create(
            title="Elective",
            q=repr(Q(full_code="CIS-1200")),
            num=1,
            block_type="MAJOR",
            block_value="CIS",
        )
        degree.rules.add(named, sibling)
        plan = self.plan("inside")
        plan.degrees.add(degree)
        double_counts = resolve_double_counts(get_degree_trees([degree]))
        self.assertNotIn(sibling, double_counts.get(named, set()))


class DualPatternTest(TestCase):
    def setUp(self):
        load()
        self.person = get_user_model().objects.create_user(username="d", password="x")
        for code in ["OIDD-2340", "MGMT-2370", "INSP-1001", "STAT-4300", "CIS-1200", "MATH-1400"]:
            course(code)

    def plan_with(self, name, dual_code, left, right, variant=None):
        plan = DegreePlan.objects.create(
            name=name,
            person=self.person,
            dual_program=DualProgram.objects.get(code=dual_code) if dual_code else None,
            right_variant_id=variant.id if variant else None,
        )
        plan.degrees.add(left, right)
        return plan

    def test_m_and_t_adds_oidd_2340_and_shares_a_course(self):
        cis = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        wharton = Degree.objects.create(program="WU_BS", degree="BS", major="WH", year=2026)
        cis_rule = leaf("CIS", "CIS-1200", "MAJOR", "CIS")
        stat = leaf("Statistics", "STAT-4300", "MAJOR", "WH")
        cis.rules.add(cis_rule)
        wharton.rules.add(stat)
        from degree.models import ProgramVariant

        plan = self.plan_with(
            "mt", "MT", cis, wharton, ProgramVariant.objects.get(code="WH_NOFL_MT")
        )
        # The dual program's default variant applies even without the override.
        plan.right_variant = None
        plan.save()

        rules, rule_to, _ = map_rules_and_degrees(plan)
        titles = {rule.title for rule in rule_to}
        self.assertIn("M&T Freshman Course", titles)
        freshman = next(rule for rule in rule_to if rule.title == "M&T Freshman Course")
        selected, _, legal = allocate_rules(
            "OIDD-2340",
            rules,
            rule_to,
            map_rules_and_degrees(plan).double_counts,
            satisfied_rules=set(),
        )
        self.assertIn(freshman, selected)
        self.assertTrue(legal)

        selected, _, legal = allocate_rules(
            "STAT-4300",
            rules,
            rule_to,
            map_rules_and_degrees(plan).double_counts,
            satisfied_rules=set(),
        )
        # STAT-4300 is only on the Wharton rule in this fixture, so it is legal there.
        self.assertIn(stat, selected)
        self.assertTrue(legal)

    def test_three_degrees_keep_two_claims(self):
        from degree.utils.degree_logic import GraduateSharing

        degrees = []
        for program, major in [("EU_BSE", "CIS"), ("WU_BS", "WH"), ("AU_BA", "ECON")]:
            degree = Degree.objects.create(
                program=program,
                degree="BSE" if program != "AU_BA" else "BA",
                major=major,
                year=2026,
            )
            degree.rules.add(leaf(major, "CIS-1200", "MAJOR", major, share_targets=[]))
            degrees.append(degree)
        plan = DegreePlan.objects.create(name="three", person=self.person)
        plan.degrees.set(degrees)
        plan_rules = map_rules_and_degrees(plan)
        selected, unselected, legal = allocate_rules(
            "CIS-1200",
            plan_rules.rules_per_component,
            plan_rules.rule_to_component,
            plan_rules.double_counts,
            satisfied_rules=set(),
            policy=plan_rules.composition.policy,
            graduate_sharing=GraduateSharing(),
        )
        claimed = {
            plan_rules.rule_to_component[rule].key
            for rule in selected
            if rule in plan_rules.rule_to_component
        }
        self.assertLessEqual(len(claimed), 2)
        self.assertTrue(unselected)
        self.assertTrue(legal)

    def test_huntsman_selects_the_seminar(self):
        inst = Degree.objects.create(program="AU_BA", degree="BA", major="INST", year=2026)
        wharton = Degree.objects.create(program="WU_BS", degree="BS", major="WH", year=2026)
        plan = self.plan_with("hunt", "HUNTSMAN", inst, wharton)
        plan_rules = map_rules_and_degrees(plan)
        seminar = next(
            rule
            for rule in plan_rules.rule_to_component
            if rule.title == "Huntsman First-Year Seminar"
        )
        selected, _, _ = allocate_rules(
            "INSP-1001",
            plan_rules.rules_per_component,
            plan_rules.rule_to_component,
            plan_rules.double_counts,
            satisfied_rules=set(),
        )
        self.assertIn(seminar, selected)

    def test_uncoordinated_dual_does_not_add_m_and_t_courses(self):
        econ = Degree.objects.create(program="AU_BA", degree="BA", major="ECON", year=2026)
        wharton = Degree.objects.create(program="WU_BS", degree="BS", major="WH", year=2026)
        plan = DegreePlan.objects.create(name="uncoord", person=self.person)
        plan.degrees.add(econ, wharton)
        titles = {rule.title for rule in map_rules_and_degrees(plan).rule_to_component}
        self.assertNotIn("M&T Freshman Course", titles)
        self.assertEqual(compose(plan).kind, "cross_school_dual")

    def test_lsm_and_viper_use_plain_trees(self):
        biol = Degree.objects.create(program="AU_BA", degree="BA", major="BIOL", year=2026)
        wharton = Degree.objects.create(program="WU_BS", degree="BS", major="WH", year=2026)
        phys = Degree.objects.create(program="AU_BA", degree="BA", major="PHYS", year=2026)
        meam = Degree.objects.create(program="EU_BSE", degree="BSE", major="MEAM", year=2026)
        lsm = self.plan_with("lsm", "LSM", biol, wharton)
        viper = self.plan_with("viper", "VIPER", phys, meam)
        for plan in (lsm, viper):
            self.assertEqual(compose(plan).kind, "coordinated")
            titles = {rule.title for rule in map_rules_and_degrees(plan).rule_to_component}
            self.assertNotIn("M&T Freshman Course", titles)
            self.assertNotIn("Huntsman First-Year Seminar", titles)

    def test_m_and_t_variant_applies_once_with_a_second_wharton_concentration(self):
        cis = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2026)
        fnce = Degree.objects.create(program="WU_BS", degree="BS", major="FNCE", year=2026)
        stat = Degree.objects.create(program="WU_BS", degree="BS", major="STAT", year=2026)
        for degree in (fnce, stat):
            degree.rules.add(
                Rule.objects.create(
                    title="Capstone",
                    q=repr(Q(attributes__code__in=["WUCP"])),
                    num=1,
                    block_type="MAJOR",
                    block_value=degree.major,
                )
            )
        plan = self.plan_with("mt-stat", "MT", cis, fnce)
        plan.degrees.add(stat)

        components = {component.owner_id: component for component in compose(plan).components}
        self.assertEqual(components[cis.id].side, "left")
        self.assertEqual(components[fnce.id].side, "right")
        self.assertIsNone(components[stat.id].side)
        self.assertTrue(components[fnce.id].extra_rules)
        self.assertFalse(components[stat.id].extra_rules)
        self.assertNotIn("Capstone", {rule.title for rule in components[fnce.id].rules})
        self.assertIn("Capstone", {rule.title for rule in components[stat.id].rules})

    def test_load_removes_stale_programs_variants_and_rules(self):
        from degree.models import ProgramVariant

        old_variant = ProgramVariant.objects.create(code="OLD_V", name="Old")
        old_variant.rules.add(
            Rule.objects.create(title="Old", q="", block_type="VARIANT", block_value="OLD_V")
        )
        DualProgram.objects.create(code="OLD", name="Old", right_variant=old_variant)
        mt_root = ProgramVariant.objects.get(code="WH_NOFL_MT").rules.first()
        renamed = Rule.objects.create(
            title="Renamed", q="", block_type="VARIANT", block_value="WH_NOFL_MT", parent=mt_root
        )
        plan = DegreePlan.objects.create(
            name="old", person=self.person, dual_program=DualProgram.objects.get(code="OLD")
        )

        self.assertEqual(load(), ["OLD", "OLD_V"])
        self.assertFalse(DualProgram.objects.filter(code="OLD").exists())
        self.assertFalse(ProgramVariant.objects.filter(code="OLD_V").exists())
        self.assertFalse(Rule.objects.filter(block_value="OLD_V").exists())
        self.assertFalse(Rule.objects.filter(id=renamed.id).exists())
        plan.refresh_from_db()
        self.assertIsNone(plan.dual_program)
        self.assertEqual(load(), [])


class CollegeCreditSummaryTest(TestCase):
    def test_a_shared_major_course_counts_once(self):
        course("ECON-0100")
        person = get_user_model().objects.create_user(username="c", password="x")
        econ = Degree.objects.create(
            program="AU_BA",
            degree="BA",
            major="ECON",
            major_name="Economics",
            year=2026,
            credits=36,
        )
        math = Degree.objects.create(
            program="AU_BA",
            degree="BA",
            major="MATH",
            major_name="Mathematics",
            year=2026,
            credits=36,
        )
        writing = Rule.objects.create(
            title="Writing",
            q=repr(Q(full_code="WRIT-0010")),
            credits=Decimal(1),
            block_type="OTHER",
            block_value="U-GE",
        )
        econ_rule = Rule.objects.create(
            title="Economics",
            q=repr(Q(full_code="ECON-0100")),
            credits=Decimal(1),
            block_type="MAJOR",
            block_value="ECON",
        )
        math_rule = Rule.objects.create(
            title="Mathematics",
            q=repr(Q(full_code="ECON-0100")),
            credits=Decimal(1),
            block_type="MAJOR",
            block_value="MATH",
        )
        econ.rules.add(writing, econ_rule)
        math.rules.add(math_rule)
        plan = DegreePlan.objects.create(name="cas", person=person)
        plan.degrees.add(econ, math)
        from degree.models import Fulfillment

        fulfillment = Fulfillment.objects.create(
            degree_plan=plan, full_code="ECON-0100", semester="2023C"
        )
        fulfillment.rules.set([econ_rule, math_rule])
        summary = summarize_plan(plan, [fulfillment])
        self.assertEqual(summary["kind"], "cas_double_major")
        self.assertEqual(summary["cas"]["shared_cu"], Decimal(1))
        self.assertEqual(summary["cas"]["floor"], Decimal(36))
