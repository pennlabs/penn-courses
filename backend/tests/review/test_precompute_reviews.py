from io import StringIO

from courses.models import Instructor, Section
from review.models import Review, CachedReviewResponse
from courses.util import get_or_create_course_and_section
from review.import_utils.import_to_db import import_review
from django.core import management
from django.test import TestCase
from tests.courses.util import create_mock_data, fill_course_soft_state

TEST1_SEMESTER = "2022C"
TEST2_SEMESTER = "2014A"

def create_review(section_code, semester, instructor_name, bits, responses=100):
    _, section, _, _ = get_or_create_course_and_section(section_code, semester)
    instructor, _ = Instructor.objects.get_or_create(name=instructor_name)
    section.instructors.add(instructor)
    import_review(section, instructor, None, responses, None, bits, lambda x, y=None: None)
    fill_course_soft_state()

class PrecomputePcrReviewsCommandTestCase(TestCase):
    COMMAND_NAME = "precompute_pcr_views"

    def setUp(self):
        self.out = StringIO()
        self.err = StringIO()

        self.instructor_name = "Instructor One"
        create_review("CIS-120-001", TEST1_SEMESTER, self.instructor_name, {"instructor_quality": 4})
        self.instructor_name2 = "Instructor Two"
        create_review("CIS-120-001", TEST2_SEMESTER, self.instructor_name, {"instructor_quality": 2})
    
    def test_one_course(self):
        management.call_command(
            self.COMMAND_NAME,
            stdout=self.out,
            stderr=self.err,
        )
        num_reviews = CachedReviewResponse.objects.count()
        self.assertEqual(1, num_reviews)

    def test_two_courses(self):
        management.call_command(
            self.COMMAND_NAME,
            stdout=self.out,
            stderr=self.err,
        )
        pass