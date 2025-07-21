import json
import os

from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option

from alert.models import AddDropPeriod
from courses.models import Attribute, Course, Instructor, Meeting, NGSSRestriction, Section
from courses.util import (
    add_attributes,
    add_restrictions,
    get_or_create_course_and_section,
    invalidate_current_semester_cache,
    upsert_course_from_opendata,
)


TEST_SEMESTER = "2019A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class AddAttributesTestCase(TestCase):
    def setUp(self):
        self.ANTH_0020, self.ANTH_0020_001, _, _ = get_or_create_course_and_section(
            "ANTH-0020-001", TEST_SEMESTER
        )
        self.MUSC_0050, self.MUSC_0050_001, _, _ = get_or_create_course_and_section(
            "MUSC-0050-001", TEST_SEMESTER
        )
        self.AMTH = {"attribute_code": "AMTH", "attribute_desc": "MUSC M Tier Thre"}
        self.NUFC = {
            "attribute_code": "NUFC",
            "attribute_desc": "NUR-ADMIN-FCH Department",
        }

    def test_add_attribute(self):
        add_attributes(self.MUSC_0050, [self.AMTH])
        self.assertTrue(self.MUSC_0050.attributes.all().filter(code="AMTH").exists())
        AMTH_obj = Attribute.objects.get(code="AMTH")
        self.assertEqual("SAS", AMTH_obj.school)
        self.assertEqual(self.AMTH["attribute_desc"], AMTH_obj.description)
        self.assertEqual("SAS", AMTH_obj.school)

    def test_add_multiple_attribute(self):
        add_attributes(self.MUSC_0050, [self.AMTH, self.NUFC])
        AMTH_obj = Attribute.objects.get(code="AMTH")
        NUFC_obj = Attribute.objects.get(code="NUFC")
        self.assertEqual("NUR", NUFC_obj.school)
        self.assertIn(AMTH_obj, self.MUSC_0050.attributes.all())
        self.assertIn(NUFC_obj, self.MUSC_0050.attributes.all())

    def test_add_attribute_multiple_times(self):
        add_attributes(self.MUSC_0050, [self.AMTH])
        add_attributes(self.ANTH_0020, [self.AMTH])
        AMTH_obj = Attribute.objects.get(code="AMTH")
        self.assertIn(self.MUSC_0050, AMTH_obj.courses.all())
        self.assertIn(self.ANTH_0020, AMTH_obj.courses.all())

    def test_add_attribute_with_no_school(self):
        add_attributes(
            self.MUSC_0050,
            [{"attribute_code": "ZPRS", "attribute_desc": "VIPER seminar"}],
        )
        VPRS_obj = Attribute.objects.get(code="ZPRS")
        self.assertIsNone(VPRS_obj.school)
        self.assertIn(self.MUSC_0050, VPRS_obj.courses.all())


class AddNGSSRestrictionTestCase(TestCase):
    def setUp(self):
        self.ANTH_0020, self.ANTH_0020_001, _, _ = get_or_create_course_and_section(
            "ANTH-0020-001", TEST_SEMESTER
        )
        self.MUSC_0050, self.MUSC_0050_001, _, _ = get_or_create_course_and_section(
            "MUSC-0050-001", TEST_SEMESTER
        )
        self.PHL = {
            "restriction_code": "PHL",
            "restriction_type": "Campus",
            "restriction_desc": "Philly Campus",
        }
        self.DOLLAR = {
            "restriction_code": "DOLLAR",
            "restriction_type": "Cohort",
            "restriction_desc": "Exclusive for cohort dollar",
        }

    def test_add_multiple_restrictions_multiple_times(self):
        add_restrictions(self.MUSC_0050_001, [self.PHL, self.DOLLAR])
        add_restrictions(self.ANTH_0020_001, [self.PHL])
        PHL_obj = NGSSRestriction.objects.get(code="PHL")
        DOLLAR_obj = NGSSRestriction.objects.get(code="DOLLAR")
        self.assertIn(self.MUSC_0050_001, PHL_obj.sections.all())
        self.assertIn(self.ANTH_0020_001, PHL_obj.sections.all())
        self.assertIn(self.MUSC_0050_001, DOLLAR_obj.sections.all())


class ParseOpendataResponseTestCase(TestCase):
    def test_parse_response(self):
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if not os.path.basename(BASE_DIR).startswith("backend"):
            test_file_path = os.path.join(
                BASE_DIR, "backend/tests/courses/test-opendata.json"
            )
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
