import json
import os

from django.test import TestCase
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Course, Instructor, Meeting, Section
from courses.util import relocate_reqs_from_restrictions, upsert_course_from_opendata


TEST_SEMESTER = "2019A"


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class RelocateReqsRestsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.rests = [dict()]
        self.reqs = []

    def test_bfs(self):
        self.rests[0]["requirement_description"] = "Benjamin Franklin Seminars"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEqual(self.reqs, ["Benjamin Franklin Seminars"])

    def test_nsm(self):
        self.rests[0]["requirement_description"] = "Natural Science & Math Sector"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEqual(self.reqs, ["Natural Science & Math Sector"])

    def test_hss(self):
        self.rests[0]["requirement_description"] = "Humanities & Social Science Sector"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEqual(self.reqs, ["Humanities & Social Science Sector"])

    def test_mixed(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]["requirement_description"] = "Benjamin Franklin Seminars"
        self.rests[1]["requirement_description"] = "Natural Science & Math Sector"
        self.rests[2]["requirement_description"] = "Humanities & Social Science Sector"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEquals(len(self.reqs), 3)
        self.assertTrue(
            "Humanities & Social Science Sector" in self.reqs
            and "Natural Science & Math Sector" in self.reqs
            and "Benjamin Franklin Seminars" in self.reqs
        )

    def test_none(self):
        self.rests[0]["requirement_description"] = "Random restriction"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEquals(len(self.reqs), 0)

    def test_mixed_other(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]["requirement_description"] = "Random restriction"
        self.rests[1]["requirement_description"] = "Natural Science & Math Sector"
        self.rests[2]["requirement_description"] = "Humanities & Social Science Sector"
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEquals(len(self.reqs), 2)
        self.assertTrue(
            "Humanities & Social Science Sector" in self.reqs
            and "Natural Science & Math Sector" in self.reqs
        )

    def test_different_rests(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]["requirement_description"] = "Random restriction"
        self.rests[1]["requirement_description"] = "Natural Science & Math Sector"
        self.rests[2]["requirement_description"] = "Humanities & Social Science Sector"
        relocate_reqs_from_restrictions(self.rests, self.reqs, ["Random restriction"])
        self.assertEquals(len(self.reqs), 1)
        self.assertTrue("Random restriction" in self.reqs)

    def test_mixed_other_already_populated(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]["requirement_description"] = "Random restriction"
        self.rests[1]["requirement_description"] = "Natural Science & Math Sector"
        self.rests[2]["requirement_description"] = "Humanities & Social Science Sector"
        self.reqs = ["A requirement"]
        relocate_reqs_from_restrictions(
            self.rests,
            self.reqs,
            [
                "Humanities & Social Science Sector",
                "Natural Science & Math Sector",
                "Benjamin Franklin Seminars",
            ],
        )
        self.assertEquals(len(self.reqs), 3)
        self.assertTrue(
            "Humanities & Social Science Sector" in self.reqs
            and "Natural Science & Math Sector" in self.reqs
            and "A requirement" in self.reqs
        )


class ParseOpendataResponseTestCase(TestCase):
    def test_parse_response(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.basename(BASE_DIR).startswith("backend"):
            test_file_path = os.path.join(BASE_DIR, "backend/tests/courses/test-opendata.json")
        else:
            test_file_path = os.path.join(BASE_DIR, "tests/courses/test-opendata.json")
        upsert_course_from_opendata(
            json.load(open(test_file_path, "r"))["result_data"][0], TEST_SEMESTER,
        )
        self.assertEqual(1, Course.objects.count())
        self.assertEqual(21, Section.objects.count())
        self.assertEqual(3, Meeting.objects.count())
        self.assertEqual(2, Instructor.objects.count())
