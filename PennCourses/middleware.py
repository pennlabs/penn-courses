from django.conf import settings


class SwitchboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if settings.SWITCHBOARD_TEST_APP is not None:
            app = settings.SWITCHBOARD_TEST_APP
        else:
            host = request.get_host().split(':')[0]
            app = settings.HOST_TO_APP.get(host, 'base')

        request.site = app
        # https://docs.djangoproject.com/en/2.2/topics/http/urls/#how-django-processes-a-request
        request.urlconf = f'PennCourses.urls.{app}'

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
