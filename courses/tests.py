from django.test import TestCase

from .models import *
from .util import *

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
        self.c = Course(department=Department.objects.get_or_create(code='PSCI')[0],
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
        self.assertEqual(course.department.code, 'CIS')
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


class CrosslistingTestCase(TestCase):
    def setUp(self):
        self.anch, _ = get_course_and_section('ANCH-027-401', TEST_SEMESTER)
        self.clst, _ = get_course_and_section('CLST-027-401', TEST_SEMESTER)

    def test_add_primary_listing(self):
        set_crosslistings(self.anch, '')
        self.anch.save()
        self.assertEqual(self.anch, self.anch.primary_listing)

    def test_add_existing_class(self):
        set_crosslistings(self.clst, 'ANCH-027-401')
        self.clst.save()
        clst, _ = get_course_and_section('CLST-027-401', TEST_SEMESTER)
        anch, _ = get_course_and_section('ANCH-027-401', TEST_SEMESTER)
        self.assertEqual(self.anch, clst.primary_listing)
        self.assertEqual(2, Course.objects.count())

    def test_crosslisting_set(self):
        set_crosslistings(self.clst, 'ANCH-027-401')
        set_crosslistings(self.anch, '')
        self.clst.save()
        self.anch.save()
        self.assertTrue(self.anch in self.clst.crosslistings.all())
        self.assertTrue(self.clst in self.anch.crosslistings.all())

    def test_crosslisting_newsection(self):
        set_crosslistings(self.anch, 'HIST-027-401')
        self.anch.save()
        self.assertEqual(3, Course.objects.count())


class RequirementTestCase(TestCase):
    def setUp(self):
        self.course = get_course('CIS', '120', TEST_SEMESTER)
        self.course2 = get_course('CIS', '125', TEST_SEMESTER)
        self.department = Department.objects.get(code='CIS')

        self.req1 = Requirement(semester=TEST_SEMESTER,
                                school='SAS',
                                code='TEST1',
                                name='Test 1')

        self.req2 = Requirement(semester=TEST_SEMESTER,
                                school='SAS',
                                code='TEST2',
                                name='Test 2')

        self.req1.save()
        self.req2.save()

        self.req1.departments.add(self.department)
        self.req2.courses.add(self.course)
        self.req1.overrides.add(self.course2)

    def test_requirements_nooverride(self):
        reqs = self.course.requirements
        self.assertTrue(2, len(reqs))

    def test_requirements_override(self):
        reqs = self.course2.requirements
        print(self.req1.overrides.all())
        self.assertEqual(1, len(reqs))
        self.assertEqual(self.req1, reqs[0])


class MeetingTestCase(TestCase):
    def setUp(self):
        pass


