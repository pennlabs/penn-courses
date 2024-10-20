from django.test import TestCase

from courses.models import Instructor
from courses.util import get_or_create_course_and_section
from review.models import Review, ReviewBit
from review.util import titleize


TEST_SEMESTER = "2017A"


class TitleizeTestCase(TestCase):
    def test_regular_name(self):
        names = [
            "Davis Haupt",
            "Old McDonald",
            "Brennan O'Leary",
            "H.R. Pickens, III",
            "Pope Leo XV",
        ]
        for name in names:
            raw = name.upper()
            self.assertEqual(name, titleize(raw))


class ReviewTestCase(TestCase):
    def setUp(self):
        self.instructor = Instructor(name="Teacher")
        self.instructor.save()
        self.review = Review(
            section=get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)[1],
            instructor=self.instructor,
        )
        self.review.save()

    def test_set_bits(self):
        self.review.set_averages(
            {
                "difficulty": 4,
                "course_quality": 3,
            }
        )
        self.assertEqual(2, ReviewBit.objects.count())
        self.assertEqual(4, ReviewBit.objects.get(field="difficulty").average)
