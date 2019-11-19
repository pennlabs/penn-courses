from django.test import TestCase

from courses.models import Instructor
from courses.util import get_or_create_course_and_section

from .models import Review, ReviewBit


class ReviewTestCase(TestCase):
    def setUp(self):
        self.instructor = Instructor(name='Teacher')
        self.instructor.save()
        self.review = Review(section=get_or_create_course_and_section('CIS-120-001', '2017A')[1],
                             instructor=self.instructor)
        self.review.save()

    def test_set_bits(self):
        self.review.set_scores({
            'difficulty': 4,
            'course_quality': 3,
        })
        self.assertEqual(2, ReviewBit.objects.count())
        self.assertEqual(4, ReviewBit.objects.get(field='difficulty').score)
