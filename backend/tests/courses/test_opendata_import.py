import json
import os

from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option

from alert.models import AddDropPeriod
from courses.models import Attribute, Course, Department, Instructor, Meeting, Section
from courses.util import (
    add_attributes,
    get_or_create_course_and_section,
    identify_school,
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


class IdentifySchoolTestCase(TestCase):
    def check_attribute_desc_to_school(self, desc_to_school):
        # TODO: DRY
        SCHOOL_CHOICES_REVERSE = dict(
            (desc.upper(), code.upper()) for (code, desc) in Attribute.SCHOOL_CHOICES
        )
        for attribute_desc in desc_to_school:
            self.assertEquals(
                identify_school(attribute_desc, SCHOOL_CHOICES_REVERSE),
                desc_to_school[attribute_desc],
            )

    def test_direct_school_mapping(self):
        self.check_attribute_desc_to_school(
            {
                "Wharton eCommerce Mj": "WH",
                "WH-COURSE-Joseph Whartn Schlrs": "WH",
                "Wharton MGMT Entre & Inno": "WH",
                "VET Clinical Rotation El": "VET",
                "SEAS MBIOT BTP AdvElect": "SEAS",
                "EAS-COURSE-DMD Elective": "SEAS",
                "GSE PHD EdLing LingCourse": "GSE",
                "COL-COURSE-Advanced Language": "SAS",
                "DSGN M Art Histor": "DSGN",
                "Design CERT IPD Bus El": "DSGN",
                "GSE-ADMIN-TFA Masters": "GSE",
                "NUR-SECTOR-ReaSys&Relationship": "NURS",
                "NURS MSN HCA Business Ele": "NURS",
            }
        )

    def test_sas_department(self):
        # Create EALC and HIST but not HSOC
        Department.objects.get_or_create(code="EALC")
        Department.objects.get_or_create(code="HIST")
        assert not Department.objects.filter(code="").exists("HSOC")
        self.check_attribute_desc_to_school(
            {"HIST M Pre 180": "SAS", "EALC M East Asian Are": "EALC", "HSOC M Regiona": "OTHER"}
        )

    def test_other(self):
        self.check_attribute_desc_to_school(
            {
                "UNV-SCHED-First of MultTrmCrse": "OTHER",
                "First Year": "OTHER",
                "2 Addl Mechan of Dis Crse": "OTHER",
            }
        )


class AddAttributesTestCase(TestCase):
    def setUp(self):
        self.ANTH_0020, self.ANTH_0020_001, _, _ = get_or_create_course_and_section(
            "ANTH-0020-001", TEST_SEMESTER
        )
        self.MUSC_0050, self.MUSC_0050_001, _, _ = get_or_create_course_and_section(
            "MUSC-0050-001", TEST_SEMESTER
        )
        self.AMTH = {"attribute_code": "AMTH", "attribute_desc": "MUSC M Tier Thre"}
        self.NUFC = {"attribute_code": "NUFC", "attribute_desc": "NUR-ADMIN-FCH Department"}

    def test_add_attribute(self):
        add_attributes([self.AMTH], self.MUSC_0050_001)
        self.assertTrue(self.MUSC_0050.attributes.all().filter(code="AMTH").exists())
        AMTH_obj = Attribute.objects.get(code="AMTH")
        self.assertEqual(self.AMTH["attribute_desc"], AMTH_obj.description)
        self.assertEqual("SAS", AMTH_obj.school)

    def test_add_multiple_attribute(self):
        add_attributes([self.AMTH, self.NUFC], self.MUSC_0050_001)
        AMTH_obj = Attribute.objects.get(code="AMTH")
        NUFC_obj = Attribute.objects.get(code="NUFC")
        self.assertContains(AMTH_obj, self.MUSC_0050.attributes)
        self.assertContains(NUFC_obj, self.MUSC_0050.attributes)

    def test_add_attribute_multiple_times(self):
        add_attributes([self.AMTH], self.MUSC_0050_001)
        add_attributes([self.AMTH], self.ANTH_0020_001)
        AMTH_obj = Attribute.objects.get(code="AMTH")
        self.assertContains(self.MUSC_0050, AMTH_obj.courses)
        self.assertContains(self.ANTH_0020, AMTH_obj.courses)


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
