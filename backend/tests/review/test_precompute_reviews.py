from io import StringIO
from typing import Optional

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
TEST5_SEMESTER = "2024A"
TEST6_SEMESTER = "2024B"

INSTRUCTOR_ONE = "Instructor One"
INSTRUCTOR_TWO = "Instructor Two"
INSTRUCTOR_THREE = "Instructor Three"


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

    def precompute_reviews(self, is_new_data):
        command_args = [self.COMMAND_NAME]
        if is_new_data:
            command_args.append("--new_data")

        management.call_command(
            *command_args,
            stdout=self.out,
            stderr=self.err,
        )

    def update_course_topic(self, old_course_code, new_course_code):
        old_course = Course.objects.filter(full_code=old_course_code).first()
        for new_course in Course.objects.filter(full_code=new_course_code):
            old_course_topic = old_course.topic
            new_course_topic = new_course.topic
            new_course.topic = old_course.topic
            old_course_topic.most_recent = new_course
            new_course.save()
            old_course_topic.save()

        if not new_course_topic.courses.exists():
            Topic.objects.filter(id=new_course_topic.id).first().delete()

    def setUp(self):
        self.out = StringIO()
        self.err = StringIO()

        # Same Course, Originally Different Topics
        create_review("CIS-120-001", TEST1_SEMESTER, INSTRUCTOR_ONE, {"instructor_quality": 4})

        create_review("CIS-120-002", TEST2_SEMESTER, INSTRUCTOR_TWO, {"instructor_quality": 2})

        create_review("CIS-1200-001", TEST3_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 0})

        # Individual Course
        create_review("CIS-1210-003", TEST3_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 2})

        # Courses to Switch Topics
        create_review("AFRC-1500-001", TEST1_SEMESTER, INSTRUCTOR_ONE, {"instructor_quality": 1})
        create_review("ANTH-1500-002", TEST2_SEMESTER, INSTRUCTOR_TWO, {"instructor_quality": 3})
        create_review("MUSC-1500-001", TEST3_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 1})
        self.update_course_topic("AFRC-1500", "ANTH-1500")

        self.set_runtime_option()
        self.precompute_reviews(is_new_data=False)

    def add_new_review_data(self):
        create_review("CIS-120-002", TEST5_SEMESTER, INSTRUCTOR_TWO, {"instructor_quality": 3})
        create_review("CIS-1200-001", TEST6_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 0})
        create_review("CIS-1210-004", TEST5_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 4})
        create_review("MUSC-1500-003", TEST6_SEMESTER, INSTRUCTOR_THREE, {"instructor_quality": 0})
        create_review("AFRC-1500-002", TEST5_SEMESTER, INSTRUCTOR_ONE, {"instructor_quality": 2})
        create_review("IPD-5150-101", TEST5_SEMESTER, INSTRUCTOR_ONE, {"instructor_quality": 3})
        self.update_course_topic("AFRC-1500", "ANTH-1500")

    def get_cached_review_with_courses(self, course_codes) -> Optional[CachedReviewResponse]:
        course_ids = []
        for course_code in course_codes:
            course_ids.extend(
                list(Course.objects.filter(full_code=course_code).values_list("id", flat=True))
            )

        topic_id = ".".join([str(id) for id in sorted(course_ids)])
        return CachedReviewResponse.objects.filter(topic_id=topic_id).first()

    def test_same_data_same_topics(self):
        self.precompute_reviews(is_new_data=False)

        # Test Number of Topics
        self.assertEqual(CachedReviewResponse.objects.count(), 5)

        # Test CachedReview Topic Id Construction
        cr1 = self.get_cached_review_with_courses(["CIS-120"])
        self.assertIsNotNone(cr1)
        cr2 = self.get_cached_review_with_courses(["CIS-1200"])
        self.assertIsNotNone(cr2)
        cr3 = self.get_cached_review_with_courses(["CIS-1210"])
        self.assertIsNotNone(cr3)
        cr4 = self.get_cached_review_with_courses(["AFRC-1500", "ANTH-1500"])
        self.assertIsNotNone(cr4)
        cr5 = self.get_cached_review_with_courses(["MUSC-1500"])
        self.assertIsNotNone(cr5)

        # Tests Cached Review Average Values
        self.assertEqual(cr1.response["average_reviews"]["rInstructorQuality"], 3)
        self.assertEqual(cr2.response["average_reviews"]["rInstructorQuality"], 0)
        self.assertEqual(cr3.response["average_reviews"]["rInstructorQuality"], 2)
        self.assertEqual(cr4.response["average_reviews"]["rInstructorQuality"], 2)
        self.assertEqual(cr5.response["average_reviews"]["rInstructorQuality"], 1)

    def test_same_data_new_topics(self):
        # Change Topics
        self.update_course_topic("CIS-120", "CIS-1200")
        self.update_course_topic("MUSC-1500", "AFRC-1500")
        self.precompute_reviews(is_new_data=False)

        # Test Number of Topics
        self.assertEqual(CachedReviewResponse.objects.count(), 4)

        # Test CachedReview Topic Id Construction
        cr1 = self.get_cached_review_with_courses(["CIS-120", "CIS-1200"])
        self.assertIsNotNone(cr1)
        cr2 = self.get_cached_review_with_courses(["CIS-1210"])
        self.assertIsNotNone(cr2)
        cr3 = self.get_cached_review_with_courses(["AFRC-1500", "MUSC-1500"])
        self.assertIsNotNone(cr3)
        cr4 = self.get_cached_review_with_courses(["ANTH-1500"])
        self.assertIsNotNone(cr4)

        # Tests Cached Review Average Values
        self.assertEqual(cr1.response["average_reviews"]["rInstructorQuality"], 2)
        self.assertEqual(cr2.response["average_reviews"]["rInstructorQuality"], 2)
        self.assertEqual(cr3.response["average_reviews"]["rInstructorQuality"], 1)
        self.assertEqual(cr4.response["average_reviews"]["rInstructorQuality"], 3)

    def test_new_data_same_topics(self):
        self.add_new_review_data()
        self.precompute_reviews(is_new_data=True)

        # Test Number of Topics
        self.assertEqual(CachedReviewResponse.objects.count(), 6)

        # Test CachedReview Topic Id Construction
        cr1 = self.get_cached_review_with_courses(["CIS-120"])
        self.assertIsNotNone(cr1)
        cr2 = self.get_cached_review_with_courses(["CIS-1200"])
        self.assertIsNotNone(cr2)
        cr3 = self.get_cached_review_with_courses(["CIS-1210"])
        self.assertIsNotNone(cr3)
        cr4 = self.get_cached_review_with_courses(["AFRC-1500", "ANTH-1500"])
        self.assertIsNotNone(cr4)
        cr5 = self.get_cached_review_with_courses(["MUSC-1500"])
        self.assertIsNotNone(cr5)
        cr6 = self.get_cached_review_with_courses(["IPD-5150"])
        self.assertIsNotNone(cr6)

        # Tests Cached Review Average Values
        self.assertEqual(cr1.response["average_reviews"]["rInstructorQuality"], 3)
        self.assertEqual(cr2.response["average_reviews"]["rInstructorQuality"], 0)
        self.assertEqual(cr3.response["average_reviews"]["rInstructorQuality"], 3)
        self.assertEqual(cr4.response["average_reviews"]["rInstructorQuality"], 2)
        self.assertEqual(cr5.response["average_reviews"]["rInstructorQuality"], 0.5)
        self.assertEqual(cr6.response["average_reviews"]["rInstructorQuality"], 3)

    def test_new_data_new_topics(self):
        # Change Topics
        self.add_new_review_data()
        self.update_course_topic("CIS-120", "CIS-1200")
        self.update_course_topic("MUSC-1500", "AFRC-1500")
        self.precompute_reviews(is_new_data=False)

        # Test Number of Topics
        self.assertEqual(CachedReviewResponse.objects.count(), 5)

        # Test CachedReview Topic Id Construction
        cr1 = self.get_cached_review_with_courses(["CIS-120", "CIS-1200"])
        self.assertIsNotNone(cr1)
        cr2 = self.get_cached_review_with_courses(["CIS-1210"])
        self.assertIsNotNone(cr2)
        cr3 = self.get_cached_review_with_courses(["AFRC-1500", "MUSC-1500"])
        self.assertIsNotNone(cr3)
        cr4 = self.get_cached_review_with_courses(["ANTH-1500"])
        self.assertIsNotNone(cr4)
        cr5 = self.get_cached_review_with_courses(["IPD-5150"])
        self.assertIsNotNone(cr5)

        # Tests Cached Review Average Values
        self.assertEqual(cr1.response["average_reviews"]["rInstructorQuality"], 1.8)
        self.assertEqual(cr2.response["average_reviews"]["rInstructorQuality"], 3)
        self.assertEqual(cr3.response["average_reviews"]["rInstructorQuality"], 1)
        self.assertEqual(cr4.response["average_reviews"]["rInstructorQuality"], 3)
        self.assertEqual(cr5.response["average_reviews"]["rInstructorQuality"], 3)
