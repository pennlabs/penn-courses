from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, Fulfillment, PDPBetaUser, Rule
from degree.utils.degree_logic import (
    GRADUATE_LEVEL,
    MAX_SHARED_GRADUATE_CREDITS,
    SHARED_LEVEL,
    UNDERGRADUATE_LEVEL,
    GraduateSharing,
    allocate_rules,
    course_number,
    is_graduate,
    level_allows,
    map_rules_and_degrees,
    prewarm_belongs_cache,
    prewarm_credits_cache,
    split_by_level,
)
from degree.views import update_fulfillments

from .test_double_counting import TEST_SEMESTER
from .util import set_semester


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


class FulfillmentLevelTest(GraduateSharingTest):
    """
    A submatriculant's transcript says which degree each course is on the books for: a course
    under the undergraduate record only, the graduate record only, or both. Only the last is
    double counted; the others may count toward one degree however the audits read.
    """

    def levels_of(self, full_code, level, sharing=None, rule_selected=None):
        """The levels (graduate, undergraduate) a course of `level` ends up selected for."""
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        selected, unselected, _ = allocate_rules(
            full_code,
            rules_per_degree,
            rule_to_degree,
            double_counts,
            rule_selected,
            degree_plan=self.plan,
            satisfied_rules=set(),
            graduate_sharing=sharing,
            credits_cache={full_code: Decimal(1)},
            level=level,
        )
        graduate, undergraduate = split_by_level(selected, rule_to_degree)
        offered_graduate, offered_undergraduate = split_by_level(unselected, rule_to_degree)
        return {
            "graduate": bool(graduate),
            "undergraduate": bool(undergraduate),
            "offered_graduate": bool(offered_graduate),
            "offered_undergraduate": bool(offered_undergraduate),
        }

    def test_a_graduate_only_course_never_counts_toward_the_bachelors(self):
        result = self.levels_of("CIS-5450", GRADUATE_LEVEL, GraduateSharing())
        self.assertTrue(result["graduate"])
        self.assertFalse(result["undergraduate"])
        self.assertFalse(result["offered_undergraduate"], "not even offered by hand")

    def test_an_undergraduate_only_course_never_counts_toward_the_masters(self):
        result = self.levels_of("CIS-5450", UNDERGRADUATE_LEVEL, GraduateSharing())
        self.assertTrue(result["undergraduate"])
        self.assertFalse(result["graduate"])
        self.assertFalse(result["offered_graduate"])

    def test_prior_selections_and_an_explicit_choice_cannot_cross_levels(self):
        """A course already in the plan drops the other record's rules when its level says so."""
        mse_rule = self.mse.rules.get()
        bse_rule = self.bse.rules.get()
        rules_per_degree, rule_to_degree, double_counts = map_rules_and_degrees(self.plan)
        selected, _, _ = allocate_rules(
            "CIS-5450",
            rules_per_degree,
            rule_to_degree,
            double_counts,
            bse_rule,
            degree_plan=self.plan,
            satisfied_rules=set(),
            prior_selected={mse_rule, bse_rule},
            level=GRADUATE_LEVEL,
        )
        self.assertEqual(selected, {mse_rule})

    def test_an_explicit_choice_cannot_cross_levels(self):
        """Dropping a masters-only course on a bachelors rule selects nothing there."""
        mse_rule = self.mse.rules.get()
        bse_rule = self.bse.rules.get()
        result = self.levels_of("CIS-5450", GRADUATE_LEVEL, rule_selected=bse_rule)
        self.assertFalse(result["undergraduate"])
        self.assertTrue(result["graduate"])
        self.assertTrue(level_allows(GRADUATE_LEVEL, self.mse))
        self.assertFalse(level_allows(GRADUATE_LEVEL, self.bse))
        self.assertTrue(level_allows(None, self.bse), "a hand-added course may count anywhere")
        self.assertTrue(level_allows(SHARED_LEVEL, self.bse))
        self.assertIsNotNone(mse_rule)

    def test_a_shared_course_counts_toward_both_within_the_allowance(self):
        sharing = GraduateSharing()
        result = self.levels_of("CIS-5450", SHARED_LEVEL, sharing)
        self.assertTrue(result["graduate"] and result["undergraduate"])
        self.assertEqual(sharing.used, Decimal(1))

    def test_a_shared_course_past_the_allowance_keeps_only_the_bachelors(self):
        """The cap is policy; a transcript listing a fourth shared course is still capped."""
        sharing = GraduateSharing()
        sharing.take(MAX_SHARED_GRADUATE_CREDITS)
        result = self.levels_of("CIS-5450", SHARED_LEVEL, sharing)
        self.assertTrue(result["undergraduate"])
        self.assertFalse(result["graduate"])
        self.assertTrue(result["offered_graduate"])

    def test_only_shared_courses_spend_the_allowance(self):
        """Graduate-only courses leave the allowance for the courses on both records."""
        sharing = GraduateSharing()
        for full_code in GRADUATE_COURSES[:4]:
            self.levels_of(full_code, GRADUATE_LEVEL, sharing)
        self.assertEqual(sharing.used, Decimal(0))
        result = self.levels_of(GRADUATE_COURSES[4], SHARED_LEVEL, sharing)
        self.assertTrue(result["graduate"] and result["undergraduate"])

    def test_onboarding_stores_and_applies_levels(self):
        PDPBetaUser.objects.create(person=self.plan.person)
        client = APIClient()
        client.force_authenticate(user=self.plan.person)
        response = client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {
                "courses": [
                    {"sem": "2024C", "courses": ["CIS-5450", "CIS-5500"]},
                    {"sem": "2025A", "courses": ["CIS-5200"]},
                ],
                "levels": {
                    "CIS-5450": SHARED_LEVEL,
                    "CIS-5500": UNDERGRADUATE_LEVEL,
                    "CIS-5200": GRADUATE_LEVEL,
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)

        _, rule_to_degree, _ = map_rules_and_degrees(self.plan)
        expected = {
            "CIS-5450": (SHARED_LEVEL, True, True),
            "CIS-5500": (UNDERGRADUATE_LEVEL, False, True),
            "CIS-5200": (GRADUATE_LEVEL, True, False),
        }
        for full_code, (level, graduate, undergraduate) in expected.items():
            fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code=full_code)
            self.assertEqual(fulfillment.level, level)
            got_graduate, got_undergraduate = split_by_level(
                fulfillment.rules.all(), rule_to_degree
            )
            self.assertEqual(
                (bool(got_graduate), bool(got_undergraduate)), (graduate, undergraduate), full_code
            )

        # Reallocating the plan, as adding a degree does, keeps the levels.
        update_fulfillments(self.plan)
        fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code="CIS-5200")
        graduate, undergraduate = split_by_level(fulfillment.rules.all(), rule_to_degree)
        self.assertTrue(graduate)
        self.assertFalse(undergraduate)

    def test_changing_a_level_reallocates_the_course(self):
        """Off the masters record, a course loses its masters rules and gains bachelors ones."""
        set_semester()
        PDPBetaUser.objects.create(person=self.plan.person)
        client = APIClient()
        client.force_authenticate(user=self.plan.person)
        _, rule_to_degree, _ = map_rules_and_degrees(self.plan)
        url = reverse(
            "degreeplan-fulfillment-set-level",
            kwargs={"degreeplan_pk": self.plan.id, "full_code": "CIS-5450"},
        )
        Fulfillment.objects.create(degree_plan=self.plan, full_code="CIS-5450", semester="2024C")

        for level, graduate, undergraduate in [
            (GRADUATE_LEVEL, True, False),
            (UNDERGRADUATE_LEVEL, False, True),
            (SHARED_LEVEL, True, True),
            (None, True, True),
        ]:
            response = client.post(url, {"level": level}, format="json")
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.data["level"], level)
            fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code="CIS-5450")
            self.assertEqual(fulfillment.level, level)
            got = split_by_level(fulfillment.rules.all(), rule_to_degree)
            self.assertEqual((bool(got[0]), bool(got[1])), (graduate, undergraduate), level)

        response = client.post(url, {"level": "BOGUS"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_a_course_numbered_below_5000_cannot_be_marked_for_the_masters(self):
        set_semester()
        PDPBetaUser.objects.create(person=self.plan.person)
        client = APIClient()
        client.force_authenticate(user=self.plan.person)
        Fulfillment.objects.create(degree_plan=self.plan, full_code="CIS-1200", semester="2024C")
        url = reverse(
            "degreeplan-fulfillment-set-level",
            kwargs={"degreeplan_pk": self.plan.id, "full_code": "CIS-1200"},
        )

        for level in (GRADUATE_LEVEL, SHARED_LEVEL):
            response = client.post(url, {"level": level}, format="json")
            self.assertEqual(response.status_code, 400, level)
            self.assertIn("5000", response.data["level"])
        self.assertIsNone(Fulfillment.objects.get(full_code="CIS-1200").level)

        response = client.post(url, {"level": UNDERGRADUATE_LEVEL}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

    def test_onboarding_keeps_a_course_numbered_below_5000_off_the_masters_record(self):
        PDPBetaUser.objects.create(person=self.plan.person)
        client = APIClient()
        client.force_authenticate(user=self.plan.person)
        response = client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {
                "courses": [{"sem": "2024C", "courses": ["CIS-1200", "CIS-5450"]}],
                "levels": {"CIS-1200": SHARED_LEVEL, "CIS-5450": SHARED_LEVEL},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        levels = dict(
            Fulfillment.objects.filter(degree_plan=self.plan).values_list("full_code", "level")
        )
        self.assertEqual(levels, {"CIS-1200": UNDERGRADUATE_LEVEL, "CIS-5450": SHARED_LEVEL})

    def test_a_single_record_transcript_sends_no_levels(self):
        """Without levels every course may count toward any degree, as before."""
        PDPBetaUser.objects.create(person=self.plan.person)
        client = APIClient()
        client.force_authenticate(user=self.plan.person)
        response = client.post(
            reverse("onboard-from-transcript", kwargs={"degree_plan_id": self.plan.id}),
            {"courses": [{"sem": "2024C", "courses": ["CIS-5450"]}]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        fulfillment = Fulfillment.objects.get(degree_plan=self.plan, full_code="CIS-5450")
        self.assertIsNone(fulfillment.level)
        _, rule_to_degree, _ = map_rules_and_degrees(self.plan)
        graduate, undergraduate = split_by_level(fulfillment.rules.all(), rule_to_degree)
        self.assertTrue(graduate and undergraduate)


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
