from io import StringIO

from django.core import management
from django.test import TestCase

from courses.models import Course, Instructor, Topic
from courses.util import get_or_create_course_and_section
from review.import_utils.import_to_db import import_review
from review.models import CachedReviewResponse
from tests.courses.util import fill_course_soft_state


TEST1_SEMESTER = "2022C"
TEST2_SEMESTER = "2014A"
TEST3_SEMESTER = "2016C"
TEST4_SEMESTER = "2018C"


def create_review(section_code, semester, instructor_name, bits, responses=100):
    _, section, _, _ = get_or_create_course_and_section(section_code, semester)
    instructor, _ = Instructor.objects.get_or_create(name=instructor_name)
    section.instructors.add(instructor)
    import_review(section, instructor, None, responses, None, bits, lambda x, y=None: None)
    fill_course_soft_state()


class PrecomputePcrReviewsCommandTestCase(TestCase):
    OPTION_COMMAND_NAME = "setoption"
    COMMAND_NAME = "precompute_pcr_views"

    def set_runtime_option(self):
        management.call_command(
            self.OPTION_COMMAND_NAME,
            "SEMESTER",
            TEST1_SEMESTER,
            stdout=self.out,
            stderr=self.err,
        )

    def precompute_reviews(self):
        management.call_command(
            self.COMMAND_NAME,
            stdout=self.out,
            stderr=self.err,
        )

    def setUp(self):
        self.out = StringIO()
        self.err = StringIO()

        self.instructor_name = "Instructor One"
        create_review(
            "CIS-120-001", TEST1_SEMESTER, self.instructor_name, {"instructor_quality": 4}
        )
        self.instructor_name2 = "Instructor Two"
        create_review(
            "CIS-120-002", TEST2_SEMESTER, self.instructor_name2, {"instructor_quality": 2}
        )
        self.instructor_name3 = "Instructor Three"
        create_review(
            "CIS-1200-001", TEST3_SEMESTER, self.instructor_name3, {"instructor_quality": 0}
        )

    def test_one_course(self):
        self.set_runtime_option()
        self.precompute_reviews()
        num_reviews = CachedReviewResponse.objects.count()
        self.assertEqual(num_reviews, 2)
        response = CachedReviewResponse.objects.all().order_by("topic_id").first().response
        self.assertEqual(response["average_reviews"]["rInstructorQuality"], 3)

    def test_update_review(self):
        self.set_runtime_option()
        self.instructor_name4 = "Instructor Three"
        create_review(
            "CIS-120-003", TEST4_SEMESTER, self.instructor_name4, {"instructor_quality": 0}
        )
        self.precompute_reviews()
        num_reviews = CachedReviewResponse.objects.count()
        self.assertEqual(num_reviews, 2)
        response = CachedReviewResponse.objects.all().order_by("topic_id").first().response
        self.assertEqual(response["average_reviews"]["rInstructorQuality"], 2)

    def test_change_topic_recompute(self):
        old_course = Course.objects.filter(full_code="CIS-120").first()
        new_course = Course.objects.filter(full_code="CIS-1200").first()
        old_topic = old_course.topic
        new_topic = new_course.topic
        new_course.topic = old_topic
        new_course.save()
        Topic.objects.filter(id=new_topic.id).first().delete()

        self.set_runtime_option()
        self.precompute_reviews()
        num_reviews = CachedReviewResponse.objects.count()
        self.assertEqual(num_reviews, 1)
        response = CachedReviewResponse.objects.all().order_by("topic_id").first().response
        self.assertEqual(response["average_reviews"]["rInstructorQuality"], 2)
