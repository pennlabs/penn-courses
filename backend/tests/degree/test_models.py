from django.db.models import Q
from django.test import TestCase
from lark.exceptions import LarkError

from courses.util import get_or_create_course_and_section
from degree.models import Degree, Rule
from degree.utils.model_utils import q_object_parser


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
        self.parent_rule = Rule.objects.create()
        self.rule1 = Rule.objects.create(
            parent=self.parent_rule,
            q=repr(Q(full_code="CIS-1200")),
            num=1,
        )
        self.rule2 = Rule.objects.create(  # Self-contradictory rule
            parent=None,
            q=repr(Q(full_code__startswith="CIS-12", full_code__endswith="1600")),
            credits=1,
        )
        self.rule3 = Rule.objects.create(  # .5 cus / 1 course CIS-19XX classes
            parent=self.parent_rule,
            q=repr(Q(full_code__startswith="CIS-19")),
            credits=0.5,
            num=1,
        )
        self.rule4 = Rule.objects.create(  # 2 CIS classes
            parent=None,
            q=repr(Q(full_code__startswith="CIS")),
            num=2,
        )
        self.degree.rules.add(
            self.parent_rule, self.rule1, self.rule2, self.rule3, self.rule4
        )

    def test_satisfied_rule(self):
        self.assertTrue(self.rule1.evaluate([self.cis_1200.full_code]))

    def test_satisfied_multiple_courses(self):
        self.assertTrue(
            self.rule4.evaluate([self.cis_1600.full_code, self.cis_1200.full_code])
        )
        self.assertTrue(
            self.rule4.evaluate([self.cis_1910.full_code, self.cis_1200.full_code])
        )

    def test_satisfied_rule_num_courses_and_credits(self):
        self.assertTrue(self.rule3.evaluate([self.cis_1910.full_code]))

    def test_surpass_rule(self):
        self.assertTrue(
            self.rule4.evaluate(
                [
                    self.cis_1200.full_code,
                    self.cis_1910.full_code,
                    self.cis_1600.full_code,
                ]
            )
        )

    def test_unsatisfied_rule(self):
        self.assertFalse(self.rule1.evaluate([self.cis_1600.full_code]))

    def test_unsatisfiable_rule(self):
        # rule2 is self-contradicting
        self.assertFalse(
            self.rule2.evaluate([self.cis_1200.full_code, self.cis_1600.full_code])
        )

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
        self.assertFalse(self.parent_rule.evaluate([self.cis_1200.full_code]))

    def test_parent_rule_satisfied(self):
        self.assertTrue(
            self.parent_rule.evaluate(
                [self.cis_1200.full_code, self.cis_1910.full_code]
            )
        )


class DoubleCountRestrictionTest(TestCase):
    def setUp(self):
        pass

    def test_nested_rules(self):
        pass

    def test_credits_violation(self):
        pass

    def test_num_courses_violation(self):
        pass
