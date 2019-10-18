from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from courses.models import Instructor, Requirement, Section
from courses.util import create_mock_data
from options.models import Option
from plan.models import Schedule
from plan.search import TypedSearchBackend
from review.models import Review


TEST_SEMESTER = '2019A'


def set_semester():
    Option(key='SEMESTER', value=TEST_SEMESTER, value_type='TXT').save()


class TypedSearchBackendTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.search = TypedSearchBackend()

    def test_type_course(self):
        req = self.factory.get('/', {'type': 'course', 'search': 'ABC123'})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(['full_code'], terms)

    def test_type_keyword(self):
        req = self.factory.get('/', {'type': 'keyword', 'search': 'ABC123'})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(['title', 'sections__instructors__name'], terms)

    def test_auto_course(self):
        courses = ['cis', 'CIS', 'cis120', 'anch-027', 'cis 121', 'ling-140']
        for course in courses:
            req = self.factory.get('/', {'type': 'auto', 'search': course})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(['full_code'], terms, f'search:{course}')

    def test_auto_keyword(self):
        keywords = ['rajiv', 'gandhi', 'programming', 'hello world']
        for kw in keywords:
            req = self.factory.get('/', {'type': 'auto', 'search': kw})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(['title', 'sections__instructors__name'], terms, f'search:{kw}')


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class CourseSearchTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = create_mock_data('MATH-114-001', TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_search_by_dept(self):
        response = self.client.get('/courses/', {'search': 'math', 'type': 'auto'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.data), 1)
        course_codes = [d['id'] for d in response.data]
        self.assertTrue('CIS-120' not in course_codes and 'MATH-114' in course_codes)

    def test_search_by_instructor(self):
        self.section.instructors.add(Instructor.objects.get_or_create(name='Tiffany Chang')[0])
        self.math1.instructors.add(Instructor.objects.get_or_create(name='Josh Doman')[0])
        searches = ['Tiffany', 'Chang']
        for search in searches:
            response = self.client.get('/courses/', {'search': search, 'type': 'auto'})
            self.assertEqual(200, response.status_code)
            self.assertEqual(len(response.data), 1)
            course_codes = [d['id'] for d in response.data]
            self.assertTrue('CIS-120' in course_codes and 'MATH-114' not in course_codes, f'search:{search}')


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class CreditUnitFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        _, self.section2 = create_mock_data('CIS-120-201', TEST_SEMESTER)
        self.section.credits = 1.0
        self.section2.credits = 0.0
        self.section.save()
        self.section2.save()
        self.client = APIClient()
        set_semester()

    def test_include_course(self):
        response = self.client.get('/courses/', {'cu': '0.5-1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_exclude_course(self):
        response = self.client.get('/courses/', {'cu': '.25-.75'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class RequirementFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = create_mock_data('MATH-114-001', TEST_SEMESTER)
        self.req = Requirement(semester=TEST_SEMESTER, code='REQ', school='SAS')
        self.req.save()
        self.req.courses.add(self.math)
        self.client = APIClient()
        set_semester()

    def test_return_all_courses(self):
        response = self.client.get('/courses/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_filter_for_req(self):
        response = self.client.get('/courses/', {'requirements': 'REQ@SAS'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual('MATH-114', response.data[0]['id'])

    def test_multi_req(self):
        course3, section3 = create_mock_data('CIS-240-001', TEST_SEMESTER)
        req2 = Requirement(semester=TEST_SEMESTER, code='REQ2', school='SEAS')
        req2.save()
        req2.courses.add(course3)

        response = self.client.get('/courses/', {'requirements': 'REQ@SAS,REQ2@SEAS'})
        self.assertEqual(2, len(response.data))


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class CourseReviewAverageTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        _, self.section2 = create_mock_data('CIS-120-002', TEST_SEMESTER)
        self.instructor = Instructor(name='Person1')
        self.instructor.save()
        self.rev1 = Review(section=create_mock_data('CIS-120-003', '2005C')[1], instructor=self.instructor)
        self.rev1.save()
        self.rev1.set_scores({
            'course_quality': 4,
            'instructor_quality': 4,
            'difficulty': 4,
        })
        self.instructor2 = Instructor(name='Person2')
        self.instructor2.save()
        self.rev2 = Review(section=create_mock_data('CIS-120-002', '2015A')[1], instructor=self.instructor2)
        self.rev2.instructor = self.instructor2
        self.rev2.save()
        self.rev2.set_scores({
            'course_quality': 2,
            'instructor_quality': 2,
            'difficulty': 2,
        })

        self.section.instructors.add(self.instructor)
        self.section2.instructors.add(self.instructor2)
        self.client = APIClient()
        set_semester()

    def test_course_average(self):
        response = self.client.get('/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.data['course_quality'])
        self.assertEqual(3, response.data['instructor_quality'])
        self.assertEqual(3, response.data['difficulty'])

    def test_section_reviews(self):
        response = self.client.get('/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data['sections']))

    def test_section_no_duplicates(self):
        instructor3 = Instructor(name='person3')
        instructor3.save()
        rev3 = Review(section=self.rev2.section, instructor=instructor3)
        rev3.save()
        rev3.set_scores({
            'course_quality': 1,
            'instructor_quality': 1,
            'difficulty': 1,
        })
        self.section2.instructors.add(instructor3)
        response = self.client.get('/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data['sections']))

    def test_filter_courses_by_review_included(self):
        response = self.client.get('/courses/', {'difficulty': '2.5-3.5'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_filter_courses_by_review_excluded(self):
        response = self.client.get('/courses/', {'difficulty': '0-2'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class GetScheduleTest(TestCase):
    def setUp(self):
        self.s = Schedule(person=User.objects.create_user(username='jacob', email='jacob@…', password='top_secret'),
                          section=Section(),
                          semester=TEST_SEMESTER,
                          name='My Test Schedule',
                          )
        self.s.save()
