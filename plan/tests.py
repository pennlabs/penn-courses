import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from options.models import Option
from rest_framework.test import APIClient

from courses.models import Instructor, Requirement
from courses.util import create_mock_data, create_mock_data_with_reviews, get_average_reviews
from plan.models import Schedule
from plan.search import TypedCourseSearchBackend
from review.models import Review


TEST_SEMESTER = '2019C'


def set_semester():
    Option(key='SEMESTER', value=TEST_SEMESTER, value_type='TXT').save()


class TypedSearchBackendTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.search = TypedCourseSearchBackend()

    def test_type_course(self):
        req = self.factory.get('/', {'type': 'course', 'search': 'ABC123'})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(['^full_code'], terms)

    def test_type_keyword(self):
        req = self.factory.get('/', {'type': 'keyword', 'search': 'ABC123'})
        terms = self.search.get_search_fields(None, req)
        self.assertEqual(['title', 'sections__instructors__name'], terms)

    def test_auto_course(self):
        courses = ['cis', 'CIS', 'cis120', 'anch-027', 'cis 121', 'ling-140']
        for course in courses:
            req = self.factory.get('/', {'type': 'auto', 'search': course})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(['^full_code'], terms, f'search:{course}')

    def test_auto_keyword(self):
        keywords = ['rajiv', 'gandhi', 'programming', 'hello world']
        for kw in keywords:
            req = self.factory.get('/', {'type': 'auto', 'search': kw})
            terms = self.search.get_search_fields(None, req)
            self.assertEqual(['title', 'sections__instructors__name'], terms, f'search:{kw}')


@override_settings(ROOT_URLCONF='PennCourses.urls.api')
class CourseSearchTestCase(TestCase):
    def setUp(self):
        self.course, self.section = create_mock_data('CIS-120-001', TEST_SEMESTER)
        self.math, self.math1 = create_mock_data('MATH-114-001', TEST_SEMESTER)
        self.client = APIClient()
        set_semester()

    def test_search_by_dept(self):
        response = self.client.get('/api/plan/courses/', {'search': 'math', 'type': 'auto'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.data), 1)
        course_codes = [d['id'] for d in response.data]
        self.assertTrue('CIS-120' not in course_codes and 'MATH-114' in course_codes)

    def test_search_by_instructor(self):
        self.section.instructors.add(Instructor.objects.get_or_create(name='Tiffany Chang')[0])
        self.math1.instructors.add(Instructor.objects.get_or_create(name='Josh Doman')[0])
        searches = ['Tiffany', 'Chang']
        for search in searches:
            response = self.client.get('/api/plan/courses/', {'search': search, 'type': 'auto'})
            self.assertEqual(200, response.status_code)
            self.assertEqual(len(response.data), 1)
            course_codes = [d['id'] for d in response.data]
            self.assertTrue('CIS-120' in course_codes and 'MATH-114' not in course_codes, f'search:{search}')


@override_settings(ROOT_URLCONF='PennCourses.urls.api')
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
        response = self.client.get('/api/plan/courses/', {'cu': '1.0'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_include_multiple(self):
        response = self.client.get('/api/plan/courses/', {'cu': '0.5,1.0'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_exclude_course(self):
        response = self.client.get('/api/plan/courses/', {'cu': '.5,1.5'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(ROOT_URLCONF='PennCourses.urls.api')
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
        response = self.client.get('/api/plan/courses/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))

    def test_filter_for_req(self):
        response = self.client.get('/api/plan/courses/', {'requirements': 'REQ@SAS'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual('MATH-114', response.data[0]['id'])

    def test_multi_req(self):
        course3, section3 = create_mock_data('CIS-240-001', TEST_SEMESTER)
        req2 = Requirement(semester=TEST_SEMESTER, code='REQ2', school='SEAS')
        req2.save()
        req2.courses.add(course3)

        response = self.client.get('/api/plan/courses/', {'requirements': 'REQ@SAS,REQ2@SEAS'})
        self.assertEqual(0, len(response.data))

    def test_double_count_req(self):
        req2 = Requirement(semester=TEST_SEMESTER, code='REQ2', school='SEAS')
        req2.save()
        req2.courses.add(self.math)
        response = self.client.get('/api/plan/courses/', {'requirements': 'REQ@SAS,REQ2@SEAS'})
        self.assertEqual(1, len(response.data))
        self.assertEqual('MATH-114', response.data[0]['id'])


@override_settings(ROOT_URLCONF='PennCourses.urls.api')
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
        response = self.client.get('/api/plan/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(3, response.data['course_quality'])
        self.assertEqual(3, response.data['instructor_quality'])
        self.assertEqual(3, response.data['difficulty'])

    def test_section_reviews(self):
        response = self.client.get('/api/plan/courses/CIS-120/')
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
        response = self.client.get('/api/plan/courses/CIS-120/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data['sections']))
        self.assertEqual(1.5, response.data['sections'][1]['course_quality'], response.data['sections'][1])

    def test_filter_courses_by_review_included(self):
        response = self.client.get('/api/plan/courses/', {'difficulty': '2.5-3.5'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))

    def test_filter_courses_by_review_excluded(self):
        response = self.client.get('/api/plan/courses/', {'difficulty': '0-2'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))


@override_settings(ROOT_URLCONF='PennCourses.urls.api')
class ScheduleTest(TestCase):
    def setUp(self):
        set_semester()
        _, self.cis120, self.cis120_reviews = create_mock_data_with_reviews('CIS-120-001', TEST_SEMESTER, 2)
        self.s = Schedule(person=User.objects.create_user(username='jacob',
                                                          email='jacob@example.com',
                                                          password='top_secret'),
                          semester=TEST_SEMESTER,
                          name='My Test Schedule')
        self.s.save()
        self.s.sections.set([self.cis120])
        self.client = APIClient()
        self.client.login(username='jacob', password='top_secret')

    def check_serialized_section(self, serialized_section, section, reviews, consider_review_data):
        self.assertEqual(section.full_code, serialized_section.get('id'))
        self.assertEqual(section.status, serialized_section.get('status'))
        self.assertEqual(section.activity, serialized_section.get('activity'))
        self.assertEqual(section.credits, serialized_section.get('credits'))
        self.assertEqual(section.semester, serialized_section.get('semester'))

        if consider_review_data:
            fields = ['course_quality', 'instructor_quality', 'difficulty', 'work_required']
            for field in fields:
                expected = get_average_reviews(reviews, field)
                actual = serialized_section.get(field)
                self.assertAlmostEqual(expected, actual, 3)

    def test_get_schedule(self):
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'My Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 1)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      self.cis120, self.cis120_reviews, True)

    def test_create_schedule(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[1]['name'], 'New Test Schedule')
        self.assertEqual(response.data[1]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[1]['sections']), 2)
        self.check_serialized_section(response.data[1]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[1]['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_create_schedule_no_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', '1739C', 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', '1739C', 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001',
                                                              'semester': '1739C'},
                                                             {'id': 'CIS-160-001',
                                                              'semester': '1739C'}]}),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[1]['name'], 'New Test Schedule')
        self.assertEqual(response.data[1]['semester'], '1739C')
        self.assertEqual(len(response.data[1]['sections']), 2)
        self.check_serialized_section(response.data[1]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[1]['sections'][1],
                                      cis160, cis160_reviews, True)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id+1) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], '1739C')
        self.check_serialized_section(response.data['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_no_semester(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', '1739C', 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', '1739C', 2)
        response = self.client.put('/api/plan/schedules/' + str(self.s.id) + '/',
                                   json.dumps({'name': 'New Test Schedule',
                                               'sections': [{'id': 'CIS-121-001', 'semester': '1739C'},
                                                            {'id': 'CIS-160-001', 'semester': '1739C'}]}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'New Test Schedule')
        self.assertEqual(response.data[0]['semester'], '1739C')
        self.assertEqual(len(response.data[0]['sections']), 2)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], '1739C')
        self.check_serialized_section(response.data['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_create_schedule_meetings(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'meetings': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[1]['name'], 'New Test Schedule')
        self.assertEqual(response.data[1]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[1]['sections']), 2)
        self.check_serialized_section(response.data[1]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[1]['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_specific(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.put('/api/plan/schedules/' + str(self.s.id) + '/',
                                   json.dumps({'semester': TEST_SEMESTER,
                                               'name': 'New Test Schedule',
                                               'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                            {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'New Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 2)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data['sections']), 2)
        self.check_serialized_section(response.data['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_specific_meetings(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.put('/api/plan/schedules/' + str(self.s.id) + '/',
                                   json.dumps({'semester': TEST_SEMESTER,
                                               'name': 'New Test Schedule',
                                               'meetings': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                            {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'New Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 2)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data['sections']), 2)
        self.check_serialized_section(response.data['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_specific_same_name(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.put('/api/plan/schedules/' + str(self.s.id) + '/',
                                   json.dumps({'semester': TEST_SEMESTER,
                                               'name': 'My Test Schedule',
                                               'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                            {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'My Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 2)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'My Test Schedule')
        self.assertEqual(response.data['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data['sections']), 2)
        self.check_serialized_section(response.data['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_general(self):
        _, cis121, cis121_reviews = create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'id': str(self.s.id),
                                                'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'New Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 2)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      cis121, cis121_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_update_schedule_general_same_name(self):
        _, cis160, cis160_reviews = create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'id': str(self.s.id),
                                                'semester': TEST_SEMESTER,
                                                'name': 'My Test Schedule',
                                                'sections': [{'id': 'CIS-120-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'My Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.check_serialized_section(response.data[0]['sections'][0],
                                      self.cis120, self.cis120_reviews, True)
        self.check_serialized_section(response.data[0]['sections'][1],
                                      cis160, cis160_reviews, True)

    def test_delete(self):
        response = self.client.delete('/api/plan/schedules/'+str(self.s.id)+'/')
        self.assertEqual(response.status_code, 204)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, len(response.data))

    def test_semesters_not_uniform(self):
        create_mock_data_with_reviews('CIS-121-001', '1739C', 2)
        create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': '1739C'},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Semester uniformity invariant violated.')

    def test_semesters_not_uniform_update(self):
        create_mock_data_with_reviews('CIS-121-001', '1739C', 2)
        create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'id': str(self.s.id),
                                                'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': '1739C'},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Semester uniformity invariant violated.')

    def test_schedule_dne(self):
        response = self.client.get('/api/plan/schedules/1000/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['detail'], 'Not found.')

    def test_name_already_exists(self):
        create_mock_data_with_reviews('CIS-121-001', TEST_SEMESTER, 2)
        create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'My Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(400, response.status_code)

    def test_section_dne_one(self):
        create_mock_data_with_reviews('CIS-160-001', TEST_SEMESTER, 2)
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'One or more sections not found in database.')

    def test_section_dne_all(self):
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'semester': TEST_SEMESTER,
                                                'name': 'New Test Schedule',
                                                'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                             {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'One or more sections not found in database.')

    def test_user_not_logged_in(self):
        client2 = APIClient()
        response = client2.post('/api/plan/schedules/',
                                json.dumps({'semester': TEST_SEMESTER,
                                            'name': 'New Test Schedule',
                                            'sections': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                         {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                                content_type='application/json')
        self.assertEqual(403, response.status_code)
        response = client2.get('/api/plan/schedules/')
        self.assertEqual(403, response.status_code)
        response = client2.put('/api/plan/schedules/' + str(self.s.id) + '/',
                               json.dumps({'semester': TEST_SEMESTER,
                                           'name': 'New Test Schedule',
                                           'meetings': [{'id': 'CIS-121-001', 'semester': TEST_SEMESTER},
                                                        {'id': 'CIS-160-001', 'semester': TEST_SEMESTER}]}),
                               content_type='application/json')
        self.assertEqual(403, response.status_code)

    def test_create_schedule_no_semester_no_courses(self):
        response = self.client.post('/api/plan/schedules/',
                                    json.dumps({'name': 'New Test Schedule',
                                                'sections': []}),
                                    content_type='application/json')
        self.assertEqual(201, response.status_code)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.data))
        self.assertEqual(response.data[1]['name'], 'New Test Schedule')
        self.assertEqual(response.data[1]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[1]['sections']), 0)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id+1) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data['sections']), 0)

    def test_update_schedule_no_semester_no_courses(self):
        response = self.client.put('/api/plan/schedules/' + str(self.s.id) + '/',
                                   json.dumps({'name': 'New Test Schedule',
                                               'sections': []}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 202)
        response = self.client.get('/api/plan/schedules/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.data))
        self.assertEqual(response.data[0]['name'], 'New Test Schedule')
        self.assertEqual(response.data[0]['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data[0]['sections']), 0)
        response = self.client.get('/api/plan/schedules/' + str(self.s.id) + '/')
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.data['name'], 'New Test Schedule')
        self.assertEqual(response.data['semester'], TEST_SEMESTER)
        self.assertEqual(len(response.data['sections']), 0)
