from unittest.mock import patch

from django.db.models import Q
from django.test import TestCase

from degree.models import Degree, Rule
from degree.utils import parse_degreeworks


class EvaluateConditionTest(TestCase):
    def setUp(self):
        self.phys = Degree(
            program="AU_BA", degree="BA", major="PHYS", concentration="BSC", year=2023
        )
        self.cmpe = Degree(
            program="EU_BSE", degree="BSE", major="CMPE", concentration=None, year=2023
        )

    @staticmethod
    def relational_operator(left, operator, right):
        """Helper function to create a relational operator condition."""
        return {"relationalOperator": {"left": left, "operator": operator, "right": right}}

    def test_unsupported_operator(self):
        comparators = ["<", ">", "<=", ">=", "IS"]
        for comparator in comparators:
            condition = self.relational_operator("MAJOR", comparator, "PHYS")
            with self.assertRaises(LookupError):
                parse_degreeworks.evaluate_condition(condition, self.phys)

    def test_major(self):
        condition = self.relational_operator("MAJOR", "=", "PHYS")
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))
        condition = self.relational_operator("MAJOR", "<>", "PHYS")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_program(self):
        condition = self.relational_operator("PROGRAM", "=", "AU_BA")
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))
        condition = self.relational_operator("PROGRAM", "=", "EU_BSE")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_conc(self):
        condition = self.relational_operator("CONC", "=", "BSC")
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))
        condition = self.relational_operator("CONC", "<>", "BSC")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))

        # concentrations have to be exact
        condition = self.relational_operator("CONC", "=", "NONE")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_attribute(self):
        condition = self.relational_operator("ATTRIBUTE", "=", "H")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_gpa(self):
        # exact GPA comparisons evaluate to false
        condition = self.relational_operator("BANNERGPA", "=", "3.0")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        condition = self.relational_operator("BANNERGPA", "<>", "3.0")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))

        condition = self.relational_operator("BANNERGPA", ">=", "3.0")
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        condition = self.relational_operator("BANNERGPA", ">", "3.0")
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        condition = self.relational_operator("BANNERGPA", "<=", "3.0")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))
        condition = self.relational_operator("BANNERGPA", "<", "3.0")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))

        # should work with "NODATA", which is occasionally returned
        condition = self.relational_operator("BANNERGPA", "<=", "NODATA")
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))

    def test_unknown_left_side(self):
        # There are often unknown comparisons with cryptic fields like "AP48" or "LT"
        # We can guess some of them, like AP48, but it's not worth doing
        condition = self.relational_operator("AP48", "=", "4")
        self.assertIsNone(parse_degreeworks.evaluate_condition(condition, self.phys))

        condition = self.relational_operator("COLLEGE", "=", "4")
        self.assertIsNone(parse_degreeworks.evaluate_condition(condition, self.phys))

    def test_or(self):
        condition = {
            "leftCondition": self.relational_operator("MAJOR", "=", "PHYS"),
            "connector": "OR",
            "rightCondition": self.relational_operator("MAJOR", "=", "CMPE"),
        }
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_and(self):
        condition = {
            "leftCondition": self.relational_operator("MAJOR", "=", "PHYS"),
            "connector": "AND",
            "rightCondition": self.relational_operator("CONC", "=", "BSC"),
        }
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.phys.concentration = "NONE"
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))

    def test_or_with_unknown(self):
        condition = {
            "leftCondition": self.relational_operator("UNKNOWN", "=", "PHYS"),
            "connector": "OR",
            "rightCondition": self.relational_operator("CONC", "=", "BSC"),
        }
        self.assertIsNone(
            parse_degreeworks.evaluate_condition(condition["leftCondition"], self.phys)
        )
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))

    def test_and_with_unknown(self):
        condition = {
            "leftCondition": self.relational_operator("UNKNOWN", "=", "PHYS"),
            "connector": "AND",
            "rightCondition": self.relational_operator("CONC", "=", "BSC"),
        }
        self.assertIsNone(
            parse_degreeworks.evaluate_condition(condition["leftCondition"], self.phys)
        )

        # If any part of the condition is false, we should return false (not None)
        self.phys.concentration = "NONE"
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))

    def test_and_or_without_right_condition(self):
        left = self.relational_operator("MAJOR", "=", "PHYS")
        condition = {
            "leftCondition": left,
            "connector": "AND",
        }
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))
        condition = {
            "leftCondition": left,
            "connector": "OR",
        }
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.cmpe))

    def test_unknown_connector(self):
        condition = {
            "leftCondition": self.relational_operator("MAJOR", "=", "PHYS"),
            "connector": "XOR",
            "rightCondition": self.relational_operator("CONC", "=", "BSC"),
        }
        with self.assertRaises(LookupError):
            parse_degreeworks.evaluate_condition(condition, self.phys)

    def test_bad_condition(self):
        condition = {"a": "b"}
        with self.assertRaises(ValueError):
            parse_degreeworks.evaluate_condition(condition, self.phys)

    def test_nested(self):
        condition = {
            "connector": "OR",
            "leftCondition": {
                "leftCondition": {
                    "leftCondition": self.relational_operator("MAJOR", "=", "PHYS"),
                    "connector": "AND",
                    "rightCondition": self.relational_operator("CONC", "=", "BSC"),
                },
                "connector": "OR",
                "rightCondition": self.relational_operator("MAJOR", "=", "CMPE"),
            },
        }
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.cmpe))
        self.phys.concentration = "NONE"
        self.assertFalse(parse_degreeworks.evaluate_condition(condition, self.phys))


class CourseArrayParserTest(TestCase):
    def test_single_course(self):
        course_array = [
            {"discipline": "BIBB", "number": "2217"},
        ]
        expected = Q(full_code="BIBB-2217")
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_course_with_suffix(self):
        course_array = [
            {"discipline": "BIBB", "number": "2217@"},
        ]
        expected = Q(full_code__startswith="BIBB-2217")
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_course_range(self):
        course_array = [
            {"discipline": "BIBB", "number": "2000", "numberEnd": "2999"},
        ]
        expected = Q(department__code="BIBB", code__gte="2000", code__lte="2999")
        print(expected, parse_degreeworks.parse_coursearray(course_array))
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_department(self):
        course_array = [
            {"discipline": "BIBB", "number": "@"},
        ]
        expected = Q(department__code="BIBB")
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_empty_course(self):
        course_array = [
            {"discipline": "@", "number": "@"},
        ]
        expected = Q()
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_non_int_course(self):
        course_array = [
            {"discipline": "CIS", "number": "4999A"},
        ]
        expected = Q(full_code="CIS-4999A")
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_non_int_course_range(self):
        course_array = [
            {"discipline": "CIS", "number": "4999A", "numberEnd": "4999B"},
        ]
        expected = Q(department__code="CIS", code__gte="4999A", code__lte="4999B")
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))


PATCHED_Q = Q(test="test")


@patch("degree.utils.parse_degreeworks.parse_coursearray", return_value=PATCHED_Q)
@patch("degree.utils.parse_degreeworks.evaluate_condition", return_value=True)
class RuleArrayParserTest(TestCase):
    def assertRuleDuckEqual(self, a: Rule | None, b: Rule | None):
        """Check duck typing equality of two Django objects (using the __dict__ dunder)"""
        if a is b:
            return

        a_dict = a.__dict__.copy()
        b_dict = b.__dict__.copy()
        a_dict.pop("_state")
        b_dict.pop("_state")
        self.assertDictEqual(a_dict, b_dict)

    @staticmethod
    def single_rule_array(ruletype, rule_req, extra_rule_kwargs={}):
        return [{"ruleType": ruletype, "requirement": rule_req, "label": "", **extra_rule_kwargs}]

    def assertParsedRulesEqual(
        self,
        ruletype: str,
        rule_req: dict,
        expected: list[Rule],
        extra_rule_kwargs={
            "label": "",
        },
    ):
        rules = []
        parse_degreeworks.parse_rulearray(
            self.single_rule_array(ruletype, rule_req, extra_rule_kwargs=extra_rule_kwargs),
            Degree(),
            rules,
        )
        self.assertEqual(len(rules), len(expected))
        for rule, expected_rule in zip(rules, expected):
            self.assertRuleDuckEqual(rule, expected_rule)

    def setUp(self):
        self.course_requirement = {
            "courseArray": [
                {"discipline": "CIS", "number": "1200"},
            ]
        }
        self.course_a_rulearray = self.single_rule_array(
            "Course",
            {
                **self.course_requirement,
                "creditsBegin": "3.5",
            },
        )
        self.course_b_rulearray = self.single_rule_array(
            "Course",
            {
                **self.course_requirement,
                "classesBegin": "1",
            },
        )
        self.rule_a = Rule(  # corresponds to course_a_rulearray
            num=None, credits=3.5, q=repr(PATCHED_Q), parent=None
        )
        self.rule_b = Rule(num=1, credits=None, q=repr(PATCHED_Q), parent=None)

    def test_empty_rulearray(self, *mocks):
        rules = []
        parse_degreeworks.parse_rulearray([], Degree(), rules)
        self.assertListEqual(rules, [])

    def test_no_ruletype(self, *mocks):
        rule_array = [
            {
                "requirement": {
                    "classesBegin": "1",
                    "classesEnd": "2",
                    "courseArray": [
                        {"discipline": "CIS", "number": "1200"},
                    ],
                }
            }
        ]

        with self.assertRaises(KeyError):
            parse_degreeworks.parse_rulearray(rule_array, Degree(), [])

    def test_course(self, *mocks):
        with self.assertRaises(ValueError):
            parse_degreeworks.parse_rulearray(
                self.single_rule_array("Course", self.course_requirement), Degree(), []
            )

        self.assertParsedRulesEqual(
            "Course",
            {**self.course_requirement, "classesBegin": "1"},
            [Rule(num=1, credits=None, q=repr(PATCHED_Q), parent=None)],
        )
        self.assertParsedRulesEqual(
            "Course",
            {
                **self.course_requirement,
                "creditsBegin": "3.5",
            },
            [Rule(num=None, credits=3.5, q=repr(PATCHED_Q), parent=None)],
        )

    def test_course_noninteger_classes(self, *mocks):
        with self.assertRaises(ValueError):
            parse_degreeworks.parse_rulearray(
                self.single_rule_array(
                    "Course", {**self.course_requirement, "classesBegin": "1.5"}
                ),
                Degree(),
                [],
            )

    def test_course_classesbegin_is_0(self, *mocks):
        self.assertParsedRulesEqual(
            "Course",
            {
                **self.course_requirement,
                "classesBegin": "0",
                "classesEnd": "1",
                "creditsBegin": ".5",
            },
            [],
        )

    def test_course_creditsbegin_is_0(self, *mocks):
        self.assertParsedRulesEqual(
            "Course",
            {
                **self.course_requirement,
                "creditsBegin": "0",
                "creditsEnd": "1",
                "classesBegin": "1",
            },
            [],
        )

    def test_multiple_courses(self, *mocks):
        rules = []
        parse_degreeworks.parse_rulearray(
            self.course_a_rulearray + self.course_b_rulearray, Degree(), rules
        )
        self.assertEqual(len(rules), 2)
        self.assertRuleDuckEqual(rules[0], self.rule_a)
        self.assertRuleDuckEqual(rules[1], self.rule_b)

    def test_ifstmt(self, *mocks):
        ifstmt = {
            "leftCondition": {
                "relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}
            },
            "ifPart": {"ruleArray": self.course_a_rulearray},
        }
        self.assertParsedRulesEqual(
            "IfStmt",
            ifstmt,
            [Rule(num=None, credits=3.5, q=repr(PATCHED_Q), parent=None)],
            extra_rule_kwargs={"booleanEvaluation": "True"},
        )

        with patch("degree.utils.parse_degreeworks.evaluate_condition", return_value=False):
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [], extra_rule_kwargs={"booleanEvaluation": "False"}
            )

    def test_ifstmt_with_else(self, *mocks):
        ifstmt = {
            "leftCondition": {
                "relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}
            },
            "ifPart": {
                "ruleArray": self.course_a_rulearray,
            },
            "elsePart": {"ruleArray": self.course_b_rulearray},
        }

        self.assertParsedRulesEqual(
            "IfStmt", ifstmt, [self.rule_a], extra_rule_kwargs={"booleanEvaluation": "True"}
        )

        with patch("degree.utils.parse_degreeworks.evaluate_condition", return_value=False):
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [self.rule_b], extra_rule_kwargs={"booleanEvaluation": "False"}
            )

    def test_ifstmt_evaluation_with_degreeworks_evaluation(self, *mocks):
        """
        Test different combinations of our evaluation and degreeworks' evaluation
        """
        ifstmt = {
            "leftCondition": {
                "relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}
            },
            "ifPart": {
                "ruleArray": self.course_a_rulearray,
            },
            "elsePart": {"ruleArray": self.course_b_rulearray},
        }

        # When our evaluation is True
        with self.assertRaises(AssertionError):
            self.assertParsedRulesEqual(
                "IfStmt",
                ifstmt,
                [],  # this is irrelevant, we just want to test the failure
                extra_rule_kwargs={"booleanEvaluation": "False"},
            )
        with self.assertRaises(AssertionError):
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [], extra_rule_kwargs={"booleanEvaluation": "Unknown"}
            )

        with patch("degree.utils.parse_degreeworks.evaluate_condition", return_value=False):
            with self.assertRaises(AssertionError):
                self.assertParsedRulesEqual(
                    "IfStmt", ifstmt, [], extra_rule_kwargs={"booleanEvaluation": "True"}
                )
            with self.assertRaises(AssertionError):
                self.assertParsedRulesEqual(
                    "IfStmt", ifstmt, [], extra_rule_kwargs={"booleanEvaluation": "Unknown"}
                )

        with patch("degree.utils.parse_degreeworks.evaluate_condition", return_value=None):
            assert (
                parse_degreeworks.evaluate_condition(
                    {"relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}},
                    Degree(),
                )
                is None
            )
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [self.rule_b], extra_rule_kwargs={"booleanEvaluation": "False"}
            )
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [self.rule_b], extra_rule_kwargs={"booleanEvaluation": "True"}
            )
            self.assertParsedRulesEqual(
                "IfStmt", ifstmt, [self.rule_b], extra_rule_kwargs={"booleanEvaluation": "Unknown"}
            )

    def test_ifstmt_with_bad_boolean_evaluation(self, *mocks):
        with self.assertRaises(LookupError):
            self.assertParsedRulesEqual(
                "IfStmt",
                {
                    "leftCondition": {
                        "relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}
                    },
                    "ifPart": {
                        "ruleArray": self.course_a_rulearray,
                    },
                    "elsePart": {"ruleArray": self.course_b_rulearray},
                },
                [Rule()],
                extra_rule_kwargs={"booleanEvaluation": "bad"},
            )

    def test_ifstmt_with_long_rule_array(self, *mocks):
        self.assertParsedRulesEqual(
            "IfStmt",
            {
                "leftCondition": {
                    "relationalOperator": {"left": "MAJOR", "operator": "=", "right": "PHYS"}
                },
                "ifPart": {"ruleArray": self.course_a_rulearray + self.course_b_rulearray},
            },
            [self.rule_a, self.rule_b],
            extra_rule_kwargs={"booleanEvaluation": "True"},
        )

    def test_subset(self, *mocks):
        parent_rule = Rule(title="Parent", num=None, credits=None, parent=None)
        self.rule_a.parent = parent_rule  # Note: this is wiped away for the next test
        self.assertParsedRulesEqual(
            "Subset",
            {},
            [parent_rule, self.rule_a],
            extra_rule_kwargs={"label": "Parent", "ruleArray": self.course_a_rulearray},
        )

    def test_subset_no_rulearray(self, *mocks):
        # TODO: is this good behavior? I'm not sure
        self.assertParsedRulesEqual("Subset", {}, [Rule()])

    def test_unknown_ruletype(self, *mocks):
        with self.assertRaises(LookupError):
            parse_degreeworks.parse_rulearray(self.single_rule_array("Unknown", {}), Degree(), [])

    def test_other_ruletypes(self, *mocks):
        self.assertParsedRulesEqual("Complete", {}, [])
        self.assertParsedRulesEqual("Incomplete", {}, [])
        self.assertParsedRulesEqual("Noncourse", {}, [])
        self.assertParsedRulesEqual("Block", {}, [])
        self.assertParsedRulesEqual("Blocktype", {}, [])


@patch("degree.utils.parse_degreeworks.parse_rulearray", return_value=None)
class ParseDegreeWorksTest(TestCase):
    def test_empty(self, *mocks):
        pass  # TODO


class ParseDegreeWorksComplexTest(TestCase):
    def test_vlst_acs(self):
        Degree(
            program="AU_BA",
            degree="BA",
            major="VLST",
            concentration="ACS",
        )

        pass  # TODO
