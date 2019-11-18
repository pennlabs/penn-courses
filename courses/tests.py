import json

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from courses.models import Course, Department, Instructor, Meeting, Requirement, Section
from courses.util import (create_mock_data, get_course, get_course_and_section, record_update,
                          relocate_reqs_from_restrictions, separate_course_code, set_crosslistings,
                          update_course_from_record, upsert_course_from_opendata)
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
        self.assertEqual('CIS-120-001', section.full_code)
        self.assertEqual(Course.objects.count(), 2)
        self.assertEqual(course.department.code, 'CIS')
        self.assertEqual(course.code, '120')
        self.assertEqual(section.code, '001')


class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)

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
        _, section = create_mock_data(self.section.normalized, TEST_SEMESTER)
        self.assertEqual('O', section.status)


class CrosslistingTestCase(TestCase):
    def setUp(self):
        self.anch, _ = create_mock_data('ANCH-027-401', TEST_SEMESTER)
        self.clst, _ = create_mock_data('CLST-027-401', TEST_SEMESTER)

    def test_add_primary_listing(self):
        set_crosslistings(self.anch, '')
        self.anch.save()
        self.assertEqual(self.anch, self.anch.primary_listing)

    def test_add_existing_class(self):
        set_crosslistings(self.clst, 'ANCH-027-401')
        self.clst.save()
        clst, _ = create_mock_data('CLST-027-401', TEST_SEMESTER)
        anch, _ = create_mock_data('ANCH-027-401', TEST_SEMESTER)
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


@override_settings(SWITCHBOARD_TEST_APP='api')
class RequirementTestCase(TestCase):
    def setUp(self):
        set_semester()
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
        self.req3 = Requirement(semester='XXXXX',
                                school='SAS',
                                code='TEST1',
                                name='Test 1+')

        self.req1.save()
        self.req2.save()
        self.req3.save()

        self.req1.departments.add(self.department)
        self.req1.overrides.add(self.course2)
        self.req2.courses.add(self.course)
        self.req2.courses.add(self.course2)
        self.req3.departments.add(self.department)

        self.client = APIClient()

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

    def test_requirement_route(self):
        response = self.client.get(f'/current/requirements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(response.data))

    def test_requirement_route_other_sem(self):
        response = self.client.get(f'/XXXXX/requirements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.data))


class MeetingTestCase(TestCase):
    def setUp(self):
        pass


"""
API Test Cases
"""


@override_settings(SWITCHBOARD_TEST_APP='api')
class CourseListTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = create_mock_data('MATH-114-001', TEST_SEMESTER)
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
        create_mock_data('MATH-104-001', new_sem)

        response = self.client.get(f'/{TEST_SEMESTER}/courses/')
        self.assertEqual(len(response.data), 2)

        response = self.client.get(f'/{new_sem}/courses/')
        self.assertEqual(len(response.data), 1)

        response = self.client.get('/all/courses/')
        self.assertEqual(len(response.data), 3)

    def test_current_semester(self):
        new_sem = TEST_SEMESTER[:-1] + 'Z'
        create_mock_data('MATH-104-001', new_sem)
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
class CourseDetailTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        i = Instructor(name='Test Instructor')
        i.save()
        self.section.instructors.add(i)
        self.math, self.math1 = create_mock_data('MATH-114-001', TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_get_course(self):
        course, section = create_mock_data('CIS-120-201', TEST_SEMESTER)
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 2)
        self.assertEqual('Test Instructor', response.data['sections'][0]['instructors'][0])

    def test_section_cancelled(self):
        course, section = create_mock_data('CIS-120-201', TEST_SEMESTER)
        section.credits = 1
        section.status = 'X'
        section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 1, response.data['sections'])

    def test_section_no_credits(self):
        course, section = create_mock_data('CIS-120-201', TEST_SEMESTER)
        section.credits = None
        section.save()
        response = self.client.get('/all/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['id'], 'CIS-120')
        self.assertEqual(len(response.data['sections']), 1, response.data['sections'])

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


@override_settings(SWITCHBOARD_TEST_APP='api')
class RelocateReqsRestsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.rests = [dict()]
        self.reqs = []

    def test_bfs(self):
        self.rests[0]['requirement_description'] = 'Benjamin Franklin Seminars'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEqual(self.reqs, ['Benjamin Franklin Seminars'])

    def test_nsm(self):
        self.rests[0]['requirement_description'] = 'Natural Science & Math Sector'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEqual(self.reqs, ['Natural Science & Math Sector'])

    def test_hss(self):
        self.rests[0]['requirement_description'] = 'Humanities & Social Science Sector'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEqual(self.reqs, ['Humanities & Social Science Sector'])

    def test_mixed(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]['requirement_description'] = 'Benjamin Franklin Seminars'
        self.rests[1]['requirement_description'] = 'Natural Science & Math Sector'
        self.rests[2]['requirement_description'] = 'Humanities & Social Science Sector'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEquals(len(self.reqs), 3)
        self.assertTrue('Humanities & Social Science Sector' in self.reqs and
                        'Natural Science & Math Sector' in self.reqs and
                        'Benjamin Franklin Seminars' in self.reqs)

    def test_none(self):
        self.rests[0]['requirement_description'] = 'Random restriction'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEquals(len(self.reqs), 0)

    def test_mixed_other(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]['requirement_description'] = 'Random restriction'
        self.rests[1]['requirement_description'] = 'Natural Science & Math Sector'
        self.rests[2]['requirement_description'] = 'Humanities & Social Science Sector'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEquals(len(self.reqs), 2)
        self.assertTrue('Humanities & Social Science Sector' in self.reqs and
                        'Natural Science & Math Sector' in self.reqs)

    def test_different_rests(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]['requirement_description'] = 'Random restriction'
        self.rests[1]['requirement_description'] = 'Natural Science & Math Sector'
        self.rests[2]['requirement_description'] = 'Humanities & Social Science Sector'
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Random restriction'])
        self.assertEquals(len(self.reqs), 1)
        self.assertTrue('Random restriction' in self.reqs)

    def test_mixed_other_already_populated(self):
        self.rests.append(dict())
        self.rests.append(dict())
        self.rests[0]['requirement_description'] = 'Random restriction'
        self.rests[1]['requirement_description'] = 'Natural Science & Math Sector'
        self.rests[2]['requirement_description'] = 'Humanities & Social Science Sector'
        self.reqs = ['A requirement']
        relocate_reqs_from_restrictions(self.rests, self.reqs,
                                        ['Humanities & Social Science Sector',
                                         'Natural Science & Math Sector',
                                         'Benjamin Franklin Seminars'])
        self.assertEquals(len(self.reqs), 3)
        self.assertTrue('Humanities & Social Science Sector' in self.reqs and
                        'Natural Science & Math Sector' in self.reqs and
                        'A requirement' in self.reqs)


class ParseOpendataResponseTestCase(TestCase):

    def test_parse_response(self):
        upsert_course_from_opendata(json.load(open('courses/test-opendata.json', 'r'))['result_data'][0], TEST_SEMESTER)
        self.assertEqual(1, Course.objects.count())
        self.assertEqual(21, Section.objects.count())
        self.assertEqual(3, Meeting.objects.count())
        self.assertEqual(2, Instructor.objects.count())
