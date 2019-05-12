from django.test import TestCase
from django.test.client import RequestFactory

from .middleware import SwitchboardMiddleware


class SwitchboardTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.host_to_app = {
            'penncourses.org': 'courses',
            'penncoursealert.com': 'pca',
            'penncourseplan.com': 'pcp'
        }

    def assertRoute(self, route):
        def test(req):
            self.assertEqual(req.site, route)
            self.assertEqual(req.urlconf, 'PennCourses.urls.'+route)
        return test

    @staticmethod
    def assertRequest(request, func):
        middleware = SwitchboardMiddleware(func)
        middleware(request)

    def test_debug_app(self):
        with self.settings(DEBUG=True, SWITCHBOARD_DEBUG_APP='debug'):
            request = self.factory.get('/')
            self.assertRequest(request, self.assertRoute('debug'))

    def test_routing_successful(self):
        with self.settings(DEBUG=False,
                           HOST_TO_APP=self.host_to_app,
                           ALLOWED_HOSTS=self.host_to_app.keys()):

            request = self.factory.get('/', HTTP_HOST='penncoursealert.com')
            self.assertRequest(request, self.assertRoute('pca'))

    def test_routing_fallback(self):
        with self.settings(DEBUG=False,
                           HOST_TO_APP=self.host_to_app,
                           ALLOWED_HOSTS=list(self.host_to_app.keys()) + ['example.com']):

            request = self.factory.get('/', HTTP_HOST='example.com')
            self.assertRequest(request, self.assertRoute('base'))
