import asyncio
import logging

import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions


logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 5  # 1 hour
jwks_client = jwt.PyJWKClient(settings.JWKS_URI)
jwks_client_lock = asyncio.Lock()


async def get_jwks_client():
    async with jwks_client_lock:
        return jwks_client


async def refresh_jwks_client():
    global jwks_client
    while True:
        try:
            new_client = jwt.PyJWKClient(settings.JWKS_URI)
            async with jwks_client_lock:
                jwks_client = new_client
                logger.info("[JWK] JWKs client updated and cached.")
        except Exception as e:
            logger.error("[JWK] Error updating JWKs client: %s", e)
        await asyncio.sleep(REFRESH_INTERVAL)


def start_jwks_refresh():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.create_task(refresh_jwks_client())


async def verify_jwt(token):
    try:
        client = await get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token, signing_key, audience=settings.AUTH_OIDC_CLIENT_ID, algorithms=["RS256"]
        )
        return payload
    except jwt.PyJWTError:
        raise exceptions.AuthenticationFailed("Invalid JWT Token.")


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Authentication based on JWT tokens stored in cookies.
    """

    def authenticate(self, request):
        id_token = request.COOKIES.get("id_token")
        if id_token:
            payload = asyncio.run(verify_jwt(id_token))
            if payload:
                return (payload, None)
        return (AnonymousUser, None)
