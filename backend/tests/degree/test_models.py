from rest_framework import serializers
from django.db.models import Q
from django.test import TestCase
from lark.exceptions import LarkError
from courses.models import User

from courses.util import get_or_create_course_and_section
from degree.models import Degree, DegreePlan, DoubleCountRestriction, Rule, Fulfillment
from degree.utils.model_utils import q_object_parser
from django.db import IntegrityError


TEST_SEMESTER = "2023C"

class QObjectParserTest(TestCase):
    def assertParsedEqual(self, q: Q):
        self.assertEqual(q_object_parser.parse(repr(q)), q)
        self.assertEqual(repr(q_object_parser.parse(repr(q))), repr(q))

    def test_no_clause(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse(r"<Q: >")

    def test_empty_q(self):
        self.assertParsedEqual(Q())

    def test_negated_empty_q(self):
        self.assertParsedEqual(~Q())

    def test_string_condition(self):
        self.assertParsedEqual(Q(key="value"))

    def test_null_condition(self):
        self.assertParsedEqual(Q(key=None))

    def test_int_condition(self):
        self.assertParsedEqual(Q(key=100))

    def test_signed_int_condition(self):
        self.assertParsedEqual(Q(key=-100))

    def test_float_condition(self):
        self.assertParsedEqual(Q(key=1.0))

    def test_signed_float_condition(self):
        self.assertParsedEqual(Q(key=-1.0))

    def test_string_escaping(self):
        self.assertParsedEqual(Q(key='"'))
        self.assertParsedEqual(Q(key="'"))
        self.assertParsedEqual(Q(key="""""'"'"""))

    def test_and(self):
        self.assertParsedEqual(Q(key=r"value") & Q(key2=r"value2"))

    def test_or(self):
        self.assertParsedEqual(Q(key="value") | Q(key2="value2"))

    def test_nested_negations(self):
        q1 = Q(key="value")
        q2 = Q(key2="value2")
        self.assertParsedEqual(~(q1 | q2))
        self.assertParsedEqual((~q1 | q2))
        self.assertParsedEqual((q1 | ~q2))
        self.assertParsedEqual(~(q1 & q2))
        self.assertParsedEqual((~q1 & q2))
        self.assertParsedEqual((q1 & ~q2))

    def test_double_negations(self):
        self.assertParsedEqual(~~Q(key="value"))

    def test_unparseable_clause(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse(r"<Q: (XOR: ('key', 'value'))>")

    def test_unparseable_value(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse(
                r"<Q: (AND: ('key', datetime.datetime(2023, 10, 11, 1, 24, 6, 114278)))>"
            )

    def test_idempotency(self):
        self.assertParsedEqual(q_object_parser.parse(repr(Q(key="\"'value"))))

    def test_empty_string(self):
        with self.assertRaises(LarkError):
            q_object_parser.parse("")


class RuleEvaluationTest(TestCase):
    def setUp(self):
        self.cis_1200, self.cis_1200_001, _, _ = get_or_create_course_and_section(
            "CIS-1200-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1600, self.cis_1600_001, _, _ = get_or_create_course_and_section(
            "CIS-1600-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1600, self.cis_1600_001, _, _ = get_or_create_course_and_section(
            "CIS-1600-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1910, self.cis_1910_001, _, _ = get_or_create_course_and_section(
            "CIS-1910-001", TEST_SEMESTER, course_defaults={"credits": 0.5}
        )

        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CIS", year=2023
        )

        self.root_rule = Rule.objects.create(
            degree=self.degree
        )
        self.rule1 = Rule.objects.create(
            degree=self.degree,
            parent=self.root_rule,
            q=repr(Q(full_code="CIS-1200")),
            num=1,
        )
        self.rule2 = Rule.objects.create(  # Self-contradictory rule
            degree=self.degree,
            parent=None,  # For now...
            q=repr(Q(full_code__startswith="CIS-12", full_code__endswith="1600")),
            credits=1,
        )
        self.rule3 = Rule.objects.create(  # .5 cus / 1 course CIS-19XX classes
            degree=self.degree,
            parent=self.root_rule,
            q=repr(Q(full_code__startswith="CIS-19")),
            credits=0.5,
            num=1,
        )
        self.rule4 = Rule.objects.create(  # 2 CIS classes
            degree=self.degree,
            parent=None,
            q=repr(Q(full_code__startswith="CIS")),
            num=2,
        )

    def test_satisfied_rule(self):
        self.assertTrue(self.rule1.evaluate([self.cis_1200.full_code]))

    def test_satisfied_multiple_courses(self):
        self.assertTrue(self.rule4.evaluate([self.cis_1600.full_code, self.cis_1200.full_code]))
        self.assertTrue(self.rule4.evaluate([self.cis_1910.full_code, self.cis_1200.full_code]))

    def test_satisfied_rule_num_courses_and_credits(self):
        self.assertTrue(self.rule3.evaluate([self.cis_1910.full_code]))

    def test_surpass_rule(self):
        self.assertTrue(
            self.rule4.evaluate(
                [self.cis_1200.full_code, self.cis_1910.full_code, self.cis_1600.full_code]
            )
        )

    def test_unsatisfied_rule(self):
        self.assertFalse(self.rule1.evaluate([self.cis_1600.full_code]))

    def test_unsatisfiable_rule(self):
        # rule2 is self-contradicting
        self.assertFalse(self.rule2.evaluate([self.cis_1200.full_code, self.cis_1600.full_code]))

    def test_nonexistent_course(self):
        # CIS-1857 doesn't exist
        self.assertFalse(self.rule4.evaluate("CIS-1857"))

    def test_unsatisfied_rule_num_courses(self):
        self.assertFalse(self.rule4.evaluate([self.cis_1200.full_code]))

    def test_unsatisfied_rule_credits(self):
        self.rule3.credits = 1.5
        self.rule3.save()
        self.assertFalse(self.rule3.evaluate([self.cis_1910.full_code]))

    def test_unsatisfied_rule_num_courses_credits(self):
        self.rule3.credits = 1.5
        self.rule3.num = 2
        self.rule3.save()
        self.assertFalse(self.rule3.evaluate([self.cis_1910.full_code]))

    def test_parent_rule_unsatisfied(self):
        self.assertFalse(self.root_rule.evaluate([self.cis_1200.full_code]))

    def test_parent_rule_satisfied(self):
        self.assertTrue(
            self.root_rule.evaluate([self.cis_1200.full_code, self.cis_1910.full_code])
        )

class FulfillmentTest(TestCase):
    """
    Test cases for the Fulfillment model.

    Most tests are related to the overriden `.save()` method, which relies on
    logic from the DoubleCountRestriction and Rule models; that logic is tested
    in the test cases for those respective rules.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )
        self.cis_1200, self.cis_1200_001, _, _ = get_or_create_course_and_section(
            "CIS-1200-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1910, self.cis_1910_001, _, _ = get_or_create_course_and_section(
            "CIS-1910-001", TEST_SEMESTER, course_defaults={"credits": 0.5}
        )
        self.cis_1930, self.cis_1930_001, _, _ = get_or_create_course_and_section(
            "CIS-1920-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )

        self.degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CIS", year=2023
        )
        self.parent_rule = Rule.objects.create(degree=self.degree)
        self.rule1 = Rule.objects.create(
            degree=self.degree,
            parent=self.parent_rule,
            q=repr(Q(full_code="CIS-1200")),
            num=1,
        )
        self.rule2 = Rule.objects.create(  # .5 cus / 1 course CIS-19XX classes
            degree=self.degree,
            parent=self.parent_rule,
            q=repr(Q(full_code__startswith="CIS-19")),
            credits=0.5,
            num=1,
        )
        self.rule3 = Rule.objects.create(  # 2 CIS classes
            degree=self.degree,
            parent=None,
            q=repr(Q(full_code__startswith="CIS")),
            num=2,
        )

        self.double_count_restriction = DoubleCountRestriction.objects.create(
            rule=self.rule2, # CIS-19XX
            other_rule=self.rule3, # CIS-XXXX
            max_credits=1,
        )
        self.degree_plan = DegreePlan.objects.create(
            name="Good Degree Plan",
            person=self.user,
            degree=self.degree,
        )
        self.other_degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CMPE", year=2023
        )
        self.bad_degree_plan = DegreePlan.objects.create(
            name="Bad Degree Plan",
            person=self.user,
            degree=self.other_degree, # empty degree
        )
    
    # TODO: this test feels mildly useless...
    def test_creation(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
        )
        fulfillment.save()
        fulfillment.rules.add(self.rule1, self.rule3)

    def test_creation_without_semester(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            rules=[self.rule1]
        )
        fulfillment.save()

    def test_duplicate_full_code(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule1]
        )
        fulfillment.save()

        other_fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule3]
        )

        try:
            other_fulfillment.save()
            self.fail("No exception raised.")
        except IntegrityError:
            pass

    def test_fulfill_rule_of_wrong_degree(self):
        fulfillment = Fulfillment(
            degree_plan=self.bad_degree_plan, # has no rules 
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule1]
        )
        try:
            fulfillment.save()
            self.fail("No exception raised.")
        except serializers.ValidationError:
            pass # OK


    def test_fulfill_nested_rule_of_wrong_degree(self):
        fulfillment = Fulfillment(
            degree_plan=self.bad_degree_plan, # has no rules 
            full_code=self.cis_1910_001.full_code,
            semester=TEST_SEMESTER,
            rules=[self.parent_rule]
        )
        try:
            fulfillment.save()
            self.fail("No exception raised.")
        except serializers.ValidationError:
            pass # OK

    def test_double_count_violation(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1910_001.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule2, self.rule3]
        )
        fulfillment.save()

        other_fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1920_001.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule2, self.rule3]
        )
        try:
            other_fulfillment.save()
            self.fail("No exception raised.")
        except DoubleCountException as e:
            self.assertEquals(e.detail, [self.double_count_restriction.id])
            pass # OK

    def test_multiple_double_count_violations(self):
        self.fail("unimplemented")

    def test_rule_violation_on_credits(self): # rule_violation
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1930.full_code, # 1 CU course
            semester=TEST_SEMESTER,
            rules=[self.rule2] # 0.5 CU rule
        )
        try:
            fulfillment.save()
            self.fail("No exception raised.")
        except RuleViolationException as e:
            self.assertEquals(e.detail, [self.rule2.id])
            pass
    
    def test_rule_violation_on_courses(self): # rule_violation
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1930.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule3]
        )
        fulfillment.save()
        
        other_fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule3]
        )
        try:
            other_fulfillment.save()
            self.fail("No exception raised.")
        except RuleViolationException as e:
            self.assertEquals(e.detail, [self.rule3.id])
            pass
    
    def test_multiple_rule_violations(self): # rule_violation
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1930.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule3, self.rule2]
        )
        fulfillment.save()
        
        other_fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule3]
        )
        try:
            other_fulfillment.save()
            self.fail("No exception raised.")
        except RuleViolationException as e:
            self.assertEquals(e.detail, [self.rule3.id, self.rule2.id])
            pass

    def test_fulfill_non_leaf_rule(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1910.full_code,
            semester=TEST_SEMESTER,
            rules=[self.parent_rule]
        )

        fulfillment.save()
        # TODO: figure out what the right exception is here and put in try-except 
        self.fail("No exception raised.")

    def test_update_fulfilled_rules_causes_rule_violation(self):
        fulfillment = Fulfillment(
            degree_plan=self.degree_plan,
            full_code=self.cis_1200.full_code,
            semester=TEST_SEMESTER,
            rules=[self.rule1]
        )
        fulfillment.save()
        try:        
            fulfillment.rules.add(self.rule2) # CIS-1900!
            # TODO: do we need an explicit save here?
            self.fail("No exception raised.")
        except RuleViolationException:
            pass # OK

    def test_status_updates(self):
        self.fail("unimplemented") # TODO: should this be tested here?

    def test_fulfill_with_old_code(self):
        # TODO: is this the responsibility of the Rule or the Fulfillment?
        self.fail("unimplemented")

    def test_fulfill_with_nonexistent_code(self):
        # TODO: does nonexistent code mean the fullfillment is wrong? or that the courses we have in our DB are incomplete?        
        self.fail("unimplemented")


class DoubleCountRestrictionTest(TestCase):
    def setUp(self):
        pass

    def test_nested_rules(self):
        pass

    def test_credits_violation(self):
        pass

    def test_num_courses_violation(self):
        pass