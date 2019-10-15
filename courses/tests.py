from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from courses.models import Course, Department, Requirement, Section
from courses.util import (get_course, get_course_and_section, record_update,
                          separate_course_code, set_crosslistings, update_course_from_record)
from options.models import Option


TEST_SEMESTER = '2019A'


def set_semester():
    Option(key='SEMESTER', value=TEST_SEMESTER, value_type='TXT').save()


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
        get_course('CIS', '120', '2012A')  # dummy course to make sure we're filtering by semester
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
        self.req2.courses.add(self.course2)
        self.req1.overrides.add(self.course2)

    def assertCoursesEqual(self, expected, actual):
        def get_codes(x): sorted([f'{c.department.code}-{c.code}' for c in x])
        self.assertEqual(get_codes(expected), get_codes(actual))

    def test_requirements_nooverride(self):
        reqs = self.course.requirements
        self.assertTrue(2, len(reqs))

    def test_requirements_override(self):
        reqs = self.course2.requirements
        self.assertEqual(1, len(reqs))
        self.assertEqual(self.req2, reqs[0])

    def test_satisfying_courses(self):
        # make it so req1 has one department-level requirement, one course-level one, and one override.
        c1 = get_course('MEAM', '101', TEST_SEMESTER)
        self.req1.courses.add(c1)
        courses = self.req1.satisfying_courses.all()
        self.assertEqual(2, len(courses))

        self.assertCoursesEqual([self.course, c1], courses)

    def test_override_precedent(self):
        # even if a course is in the list of courses, don't include it if it's in the list of overrides
        self.req1.courses.add(self.course2)
        courses = self.req1.satisfying_courses.all()
        self.assertEqual(1, len(courses))
        self.assertCoursesEqual([self.course], courses)
        reqs = self.course2.requirements
        self.assertEqual(1, len(reqs))
        self.assertEqual(self.req2, reqs[0])


class MeetingTestCase(TestCase):
    def setUp(self):
        pass


"""
API Test Cases
"""


@override_settings(SWITCHBOARD_TEST_APP='api')
class CourseListTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.section.status = 'O'
        self.section.credits = 1
        self.section.save()
        self.math, self.math1 = get_course_and_section('MATH-114-001', TEST_SEMESTER)
        self.math1.status = 'O'
        self.math1.credits = 1
        self.math1.save()
        self.client = APIClient()
        set_semester()

    def test_get_courses(self):
        response = self.client.get('/all/courses/')
        self.assertEqual(len(response.data), 2)
        course_codes = [d['id'] for d in response.data]
        self.assertTrue('CIS-120' in course_codes and 'MATH-114' in course_codes)
        self.assertTrue(1, response.data[0]['num_sections'])
        self.assertTrue(1, response.data[1]['num_sections'])

    def test_semester_setting(self):
        new_sem = TEST_SEMESTER[:-1] + 'Z'
        get_course_and_section('MATH-104-001', new_sem)

        response = self.client.get(f'/{TEST_SEMESTER}/courses/')
        self.assertEqual(len(response.data), 2)

        response = self.client.get(f'/{new_sem}/courses/')
        self.assertEqual(len(response.data), 1)

        response = self.client.get('/all/courses/')
        self.assertEqual(len(response.data), 3)

    def test_current_semester(self):
        new_sem = TEST_SEMESTER[:-1] + 'Z'
        get_course_and_section('MATH-104-001', new_sem)
        response = self.client.get(f'/current/courses/')
        self.assertEqual(len(response.data), 2)

    def test_course_with_no_sections_not_in_list(self):
        self.math.sections.all().delete()
        response = self.client.get('/all/courses/')
        self.assertEqual(len(response.data), 1, response.data)

    def test_course_with_cancelled_sections_not_in_list(self):
        self.math1.status = 'X'
        self.math1.save()
        response = self.client.get('/all/courses/')
        self.assertEqual(response.data[1]['num_sections'], 0, response.data)


@override_settings(SWITCHBOARD_TEST_APP='api')
class SectionListTestCase(TestCase):
    def setUp(self):
        self.course1, self.section1 = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.course2, self.section2 = get_course_and_section('CIS-120-002', TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_get_sections(self):
        response = self.client.get('/all/sections/')
        self.assertEqual(len(response.data), 2)
        codes = [d['id'] for d in response.data]
        self.assertTrue('CIS-120-001' in codes and 'CIS-120-002' in codes)


@override_settings(SWITCHBOARD_TEST_APP='api')
class CourseDetailTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.section.credits = 1
        self.section.status = 'O'
        self.section.save()
        self.math, self.math1 = get_course_and_section('MATH-114-001', TEST_SEMESTER)
        self.math1.credits = 1
        self.math1.status = 'C'
        self.math1.save()
        self.client = APIClient()
        set_semester()

    def test_get_course(self):
        course, section = get_course_and_section('CIS-120-201', TEST_SEMESTER)
        section.credits = 1
        section.status = 'O'
        section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 2)

    def test_section_cancelled(self):
        course, section = get_course_and_section('CIS-120-201', TEST_SEMESTER)
        section.credits = 1
        section.status = 'X'
        section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 1)

    def test_section_no_credits(self):
        course, section = get_course_and_section('CIS-120-201', TEST_SEMESTER)
        section.status = 'O'
        section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 1)

    def test_course_no_good_sections(self):
        self.section.status = 'X'
        self.section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 0)

    def test_not_get_course(self):
        response = self.client.get('/all/courses/CIS-160/')
        self.assertEqual(response.status_code, 404)
