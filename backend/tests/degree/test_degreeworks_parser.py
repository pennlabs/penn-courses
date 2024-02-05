from django.db.models import Q
from django.test import TestCase

from degree.utils import parse_degreeworks


class ParserEvaluationTest(TestCase):
    def test_comparators(self):
        pass

    def test_and(self):
        pass

    def test_or(self):
        pass

    def test_nested(self):
        pass


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
