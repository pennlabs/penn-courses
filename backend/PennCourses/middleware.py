import threading
import time
import logging
from django.http import HttpResponseForbidden
from django.conf import settings
import jwt

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 3600  # 1 hour
jwks_client = jwt.PyJWKClient(settings.JWKS_URI)
jwks_client_lock = threading.Lock()

def get_jwks_client():
    with jwks_client_lock:
        return jwks_client

def start_jwks_refresh():
    def refresh():
        global jwks_client
        while True:
            try:
                new_client = jwt.PyJWKClient(settings.JWKS_URI)
                with jwks_client_lock:
                    jwks_client = new_client
                    logger.info("[JWK] JWKs client updated and cached.")
            except Exception as e:
                logger.info("[JWK] Error updating JWKs client: %s", e)
            time.sleep(REFRESH_INTERVAL)

    thread = threading.Thread(target=refresh, daemon=True)
    thread.start()

def verify_jwt(token):
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(token, signing_key,audience=settings.AUTH_OIDC_CLIENT_ID, algorithms=["RS256"])
        return payload
    except jwt.PyJWTError:
        raise HttpResponseForbidden("Invalid JWT token.")

class OIDCMiddleware:
    def __init__(self, get_response):
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
