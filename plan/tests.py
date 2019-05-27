from django.test import TestCase, RequestFactory, override_settings
from rest_framework.test import APIClient

from .search import TypedSearchBackend
from courses.models import *
from courses.util import *
from review.models import *
from options.models import Option

TEST_SEMESTER = '2019A'


def set_semester():
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type='TXT').save()


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
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = get_course_and_section('MATH-114-001', TEST_SEMESTER)
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
class RequirementFilterTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = get_course_and_section('MATH-114-001', TEST_SEMESTER)
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
        response = self.client.get('/courses/', {'requirement': 'REQ@SAS'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual('MATH-114', response.data[0]['id'])

    def test_req_doesnt_exist(self):
        response = self.client.get('/courses/', {'requirement': 'BLAH@SEAS'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(SWITCHBOARD_TEST_APP='pcp')
class CourseReviewAverageTestCase(TestCase):
    def setUp(self):
        self.course, self.section = get_course_and_section('CIS-120-001', TEST_SEMESTER)
        _, self.section2 = get_course_and_section('CIS-120-002', TEST_SEMESTER)
        self.instructor = Instructor(name="Person1")
        self.instructor.save()
        self.rev1 = Review(section=get_course_and_section('CIS-120-003', '2005C')[1], instructor=self.instructor)
        self.rev1.save()
        self.rev1.set_scores({
            'course_quality': 4,
            'instructor_quality': 4,
            'difficulty': 4,
        })
        self.instructor2 = Instructor(name="Person2")
        self.instructor2.save()
        self.rev2 = Review(section=get_course_and_section('CIS-120-002', '2015A')[1], instructor=self.instructor2)
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
