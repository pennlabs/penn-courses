from django.db.models import Q
from django.test import TestCase

from degree.utils import parse_degreeworks
from degree.models import Degree


class EvaluateConditionTest(TestCase):
    def setUp(self):
        self.phys = Degree(program="AU_BA", degree="BA", major="PHYS", concentration="BSC", year=2023)
        self.cmpe = Degree(program="EU_BSE", degree="BSE", major="CMPE", concentration=None, year=2023)

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
        
        condition = self.relational_operator("COLLEGE", "=","4")
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
        self.assertIsNone(parse_degreeworks.evaluate_condition(condition["leftCondition"], self.phys))
        self.assertTrue(parse_degreeworks.evaluate_condition(condition, self.phys))


    def test_and_with_unknown(self):
        condition = {
            "leftCondition": self.relational_operator("UNKNOWN", "=", "PHYS"),
            "connector": "AND",
            "rightCondition": self.relational_operator("CONC", "=", "BSC"),
        }
        self.assertIsNone(parse_degreeworks.evaluate_condition(condition["leftCondition"], self.phys))

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
            }
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
        expected = Q(department__code="BIBB", code__gte=2000, code__lte=2999)
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
            {"discipline": "CIS", "number": "not-a-number"},
        ]
        expected = Q()
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))

    def test_non_int_course_range(self):
        course_array = [
            {"discipline": "CIS", "number": "not-a-number", "numberEnd": "also-not-a-number"},
        ]
        expected = Q()
        self.assertEqual(expected, parse_degreeworks.parse_coursearray(course_array))