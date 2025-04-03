from django.conf import settings


class OIDCMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        print("MIDDLEWARE!")
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/api/review/jwt'):
            print(f"Middleware applied to: {request.path}")
            print(settings.AUTH_OIDC_CLIENT_ID)
        return None
