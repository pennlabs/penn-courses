from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Rule
from degree.utils.degree_logic import (
    MAX_SHARED_GRADUATE_CREDITS,
    GraduateSharing,
    allocate_rules,
    course_number,
    is_graduate,
    map_rules_and_degrees,
    prewarm_belongs_cache,
    prewarm_credits_cache,
    split_by_level,
)

from .test_double_counting import TEST_SEMESTER


ANY_MAJOR = [{"kind": "MAJOR", "value": None}]

# Graduate coursework a submatriculant might share, plus one undergraduate course that is not
# eligible however the audit's own policy reads.
GRADUATE_COURSES = ["CIS-5450", "CIS-5500", "CIS-5200", "CIS-5550", "CIS-5710"]
UNDERGRADUATE_COURSE = "CIS-2400"


def any_of(full_codes):
    """A Q matching any of the given courses, for a rule that accepts all of them."""
    q = Q()
    for full_code in full_codes:
        q |= Q(full_code=full_code)
    return q


class GraduateSharingTest(TestCase):
    """
    A submatriculant's bachelors and masters are separately scraped audits, and each says it
    may share with any other MAJOR block, so together they would double count without limit.
    SEAS caps that at three CUs of graduate coursework, which no audit states.
    """

    def setUp(self):
        for full_code in GRADUATE_COURSES + [UNDERGRADUATE_COURSE]:
            get_or_create_course_and_section(f"{full_code}-001", TEST_SEMESTER)

        self.bse = self.make_degree("EU_BSE", "BSE", "CSCI")
        self.mse = self.make_degree("EM_MSE", "MSE", "CIS")

        self.plan = DegreePlan.objects.create(
            name="submat",
            person=get_user_model().objects.create_user(username="submat", password="pw"),
        )
        self.plan.degrees.add(self.bse, self.mse)

    def make_degree(self, program, degree_code, major):
        """A degree whose single rule takes any of the test courses and shares with any major."""
        degree = Degree.objects.create(
            program=program, degree=degree_code, major=major, year=2026, credits=10
        )
        codes = GRADUATE_COURSES + [UNDERGRADUATE_COURSE]
        rule = Rule.objects.create(
            title=f"{major} requirement",
            block_type="MAJOR",
            block_value=major,
            share_targets=ANY_MAJOR,
            num=len(codes),
            q=repr(any_of(codes)),
        )
        degree.rules.add(rule)
        return degree

    def allocate(self, full_codes, sharing=None):
        """
        Allocates the given courses in order, as the whole-plan callers do, and returns the
        ones that ended up counting toward both levels.
        """
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        belongs = prewarm_belongs_cache(
            {rule for rules in rules_per_degree.values() for rule in rules}, full_codes
        )
        credits = prewarm_credits_cache(full_codes)

        shared = []
        for full_code in full_codes:
            selected, _, _ = allocate_rules(
                full_code,
                rules_per_degree,
                rule_to_degree,
                double_counts,
                degree_plan=self.plan,
                satisfied_rules=set(),
                belongs_cache=belongs,
                graduate_sharing=sharing,
                credits_cache=credits,
            )
            graduate, undergraduate = split_by_level(selected, rule_to_degree)
            if graduate and undergraduate:
                shared.append(full_code)
        return shared

    def test_without_the_cap_every_course_double_counts(self):
        """The behavior the audits alone produce, which the cap exists to correct."""
        self.assertEqual(self.allocate(GRADUATE_COURSES), GRADUATE_COURSES)

    def test_the_cap_limits_sharing_to_three_credits(self):
        self.assertEqual(len(self.allocate(GRADUATE_COURSES, GraduateSharing())), 3)

    def test_the_allowance_goes_to_the_earliest_courses(self):
        """Courses arrive in the order they were taken, so the first three eligible win it."""
        self.assertEqual(self.allocate(GRADUATE_COURSES, GraduateSharing()), GRADUATE_COURSES[:3])

    def test_a_capped_course_keeps_its_undergraduate_rules(self):
        """Past the allowance a course still counts toward the bachelors, just not the masters."""
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        sharing = GraduateSharing()
        sharing.take(MAX_SHARED_GRADUATE_CREDITS)  # already spent

        selected, unselected, _ = allocate_rules(
            "CIS-5450",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            degree_plan=self.plan,
            satisfied_rules=set(),
            graduate_sharing=sharing,
            credits_cache={"CIS-5450": Decimal(1)},
        )
        graduate, undergraduate = split_by_level(selected, rule_to_degree)
        self.assertTrue(undergraduate, "should still count toward the bachelors")
        self.assertFalse(graduate, "should no longer count toward the masters")
        self.assertTrue(
            any(is_graduate(rule_to_degree.get(rule)) for rule in unselected),
            "the masters rule should be offered as unselected rather than dropped",
        )

    def test_undergraduate_coursework_never_spends_the_allowance(self):
        """Only 5000+ coursework may be shared, whatever the audit's policy permits."""
        self.assertEqual(self.allocate([UNDERGRADUATE_COURSE], GraduateSharing()), [])

    def test_a_masters_only_plan_leaves_the_allowance_alone(self):
        """Nothing is shared when there is no undergraduate degree to share with."""
        self.plan.degrees.remove(self.bse)
        sharing = GraduateSharing()
        self.assertEqual(self.allocate(GRADUATE_COURSES, sharing), [])
        self.assertEqual(sharing.used, Decimal(0))


class GraduateHelpersTest(TestCase):
    def test_course_number(self):
        self.assertEqual(course_number("CIS-5200"), 5200)
        self.assertEqual(course_number("CIS-1200"), 1200)
        self.assertIsNone(course_number("NOT-A-COURSE"))
        self.assertIsNone(course_number(""))

    def test_is_graduate(self):
        self.assertTrue(is_graduate(Degree(program="EM_MSE")))
        self.assertFalse(is_graduate(Degree(program="EU_BSE")))
        self.assertFalse(is_graduate(None), "a rule of no component is not graduate")

    def test_sharing_allowance(self):
        sharing = GraduateSharing()
        self.assertTrue(sharing.allows(Decimal(3)))
        self.assertFalse(sharing.allows(Decimal("3.5")))
        sharing.take(Decimal(2))
        self.assertTrue(sharing.allows(Decimal(1)))
        self.assertFalse(sharing.allows(Decimal("1.5")))
