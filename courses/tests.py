from django.test import TestCase

from .models import *

TEST_SEMESTER = '2019A'


class SepCourseCodeTest(TestCase):
    def test_four_letter_dept_code(self):
        self.assertEqual(('ANTH', '361', '401'), separate_course_code('ANTH361401'))

    def test_three_letter_dept_code(self):
        self.assertEqual(('CIS', '120', '001'), separate_course_code('CIS 120001'))

    def test_two_letter_dept_code(self):
        self.assertEqual(('WH', '110', '001'), separate_course_code('WH  110001'))

    def test_four_letter_with_dashes(self):
        self.assertEqual(('PSCI', '110', '001'), separate_course_code('PSCI-110-001'))

    def test_three_letter_with_dashes(self):
        self.assertEqual(('CIS', '110', '001'), separate_course_code('CIS -110-001'))

    def test_two_letter_with_dashes(self):
        self.assertEqual(('WH', '110', '001'), separate_course_code('WH  -110-001'))

    def test_invalid_course(self):
        try:
            separate_course_code('BLAH BLAH BLAH')
            self.fail('Should throw exception')
        except ValueError:
            pass


class GetCourseSectionTest(TestCase):
    def setUp(self):
        self.c = Course(department='PSCI',
                        code='131',
                        semester=TEST_SEMESTER,
                        title='American Foreign Policy')
        self.c.save()
        self.s = Section(code='001', course=self.c)
        self.s.save()

    def assertCourseSame(self, s):
        course, section = get_course_and_section(s, TEST_SEMESTER)
        self.assertEqual(course, self.c, s)
        self.assertEqual(section, self.s, s)

    def test_get_course_exists_nodash(self):
        test_valid = [
            'PSCI131001',
            'PSCI 131 001',
            'PSCI 131001',
            'PSCI-131-001',
            'psci131001',
            'psci-131-001',
            'psci 131 001',
        ]
        for test in test_valid:
            self.assertCourseSame(test)

    def test_create_course(self):
        course, section = get_course_and_section('CIS 120 001', TEST_SEMESTER)
        self.assertEqual(Course.objects.count(), 2)
        self.assertEqual(course.department, 'CIS')
        self.assertEqual(course.code, '120')
        self.assertEqual(section.code, '001')


class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)

    def test_update_status(self):
        self.section.status = 'C'
        self.section.save()
        up = record_update(self.section.normalized,
                           TEST_SEMESTER,
                           'C',
                           'O',
                           True,
                           'JSON')
        up.save()
        update_course_from_record(up)
        _, section = get_course_and_section(self.section.normalized, TEST_SEMESTER)
        self.assertEqual('O', section.status)

