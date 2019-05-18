from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from .middleware import SwitchboardMiddleware


class SwitchboardTestCase(TestCase):
    host_to_app = {
        'penncourses.org': 'courses',
        'penncoursealert.com': 'pca',
        'penncourseplan.com': 'pcp'
    }
    def setUp(self):
        self.factory = RequestFactory()
        self.host_to_app = {
            'penncourses.org': 'courses',
            'penncoursealert.com': 'pca',
            'penncourseplan.com': 'pcp'
        }

    def assertRoute(self, route):
        def test(req):
            print(req.urlconf)
            self.assertEqual(route, req.site)
            self.assertEqual('PennCourses.urls.'+route, req.urlconf)
        return test

    @staticmethod
    def assertRequest(request, func):
        middleware = SwitchboardMiddleware(func)
        middleware(request)

    @override_settings(SWITCHBOARD_TEST_APP='debug')
    def test_debug_app(self):
        request = self.factory.get('/')
        self.assertRequest(request, self.assertRoute('debug'))

    @override_settings(SWITCHBOARD_TEST_APP=None, HOST_TO_APP=host_to_app, ALLOWED_HOSTS=host_to_app.keys())
    def test_routing_successful(self):
        request = self.factory.get('/', HTTP_HOST='penncoursealert.com')
        self.assertRequest(request, self.assertRoute('pca'))

    @override_settings(SWITCHBOARD_TEST_APP=None, HOST_TO_APP=host_to_app,
                       ALLOWED_HOSTS=list(host_to_app.keys()) + ['example.com'])
    def test_routing_fallback(self):
        request = self.factory.get('/', HTTP_HOST='example.com')
        self.assertRequest(request, self.assertRoute('base'))
