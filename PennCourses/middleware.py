from django.conf import settings


class SwitchboardMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if settings.DEBUG:
            app = settings.DEBUG_APP
        else:
            host, port = request.get_host().split(':')
            app = settings.HOST_TO_APP.get(host, 'base')

        request.site = app
        request.urlconf = f'PennCourses.urls.{app}'

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
