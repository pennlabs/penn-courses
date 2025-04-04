from django.conf import settings
from django.http import HttpResponseForbidden
import jwt

def verify_jwt(token):
    # TODO: cache JWK set
    print(token)
    try:
        jwks_client = jwt.PyJWKClient(settings.JWKS_URI)
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        print(signing_key)
        payload = jwt.decode(token, signing_key,audience=settings.AUTH_OIDC_CLIENT_ID, algorithms=["RS256"])
        print(payload)
        return payload
    except jwt.PyJWTError:
        raise HttpResponseForbidden("Invalid JWT token.")

class OIDCMiddleware:
    def __init__(self, get_response):
        # jwks.fetch_and_cache_jwks()
        # jwks.start_jwks_refresh()
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/review/testjwt'):
            id_token = request.COOKIES.get('id_token')
            if id_token:
                payload = verify_jwt(id_token)
                if payload:
                    return response
            return HttpResponseForbidden("Invalid Token")
        return response
