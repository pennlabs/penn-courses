import json
import os

from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option

from alert.models import AddDropPeriod
from courses.models import Course, Instructor, Meeting, Section
from courses.util import invalidate_current_semester_cache, upsert_course_from_opendata


TEST_SEMESTER = "2019A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class ParseOpendataResponseTestCase(TestCase):
    def test_parse_response(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.basename(BASE_DIR).startswith("backend"):
            test_file_path = os.path.join(BASE_DIR, "backend/tests/courses/test-opendata.json")
        else:
            test_file_path = os.path.join(BASE_DIR, "tests/courses/test-opendata.json")
        upsert_course_from_opendata(
            json.load(open(test_file_path, "r"))["result_data"][0],
            TEST_SEMESTER,
        )
        self.assertEqual(1, Course.objects.count())
        self.assertEqual(23, Section.objects.count())
        self.assertEqual(3, Meeting.objects.count())
        self.assertEqual(2, Instructor.objects.count())
