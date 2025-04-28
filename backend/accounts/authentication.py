import requests
from django.contrib import auth
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from accounts.settings import accounts_settings


User = get_user_model()


class PlatformAuthentication(authentication.BaseAuthentication):
    """
    Authentication based on access tokens created by Platform.

    Clients should authenticate by passing the access token in the "Authorization"
    HTTP header, prepended with the string "Bearer ". For example:

        Authorization: Bearer abc
    """

    keyword = "Bearer"

    # DLA receives an incoming authentication request (from another product DLA) and processes it
    def authenticate(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION", "").split()
        if not authorization or authorization[0] != self.keyword:
            return None
        if len(authorization) == 1:
            msg = "Invalid token header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(authorization) > 2:
            msg = "Invalid token header. Token string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)
        token = authorization[1]
        body = {"token": token}
        headers = {"Authorization": f"Bearer {token}"}
        try:
            platform_request = requests.post(
                url=accounts_settings.PLATFORM_URL + "/accounts/introspect/",
                headers=headers,
                data=body,
            )
            if platform_request.status_code != 200:  # Access token is invalid
                raise exceptions.AuthenticationFailed("Invalid access token.")
            json = platform_request.json()
            user_props = json["user"]
            user = auth.authenticate(remote_user=user_props, tokens=False)
            if user:  # User authenticated successfully
                return (user, None)
            else:  # Error occurred
                raise exceptions.AuthenticationFailed("Invalid User.")
        except requests.exceptions.RequestException:  # Can't connect to platform
            # Throw a 403 because we can't verify the incoming access token so we
            # treat it as invalid. Ideally platform will never go down, so this
            # should never happen.
            raise exceptions.AuthenticationFailed(
                "Could not verify access token. Error connecting to platform."
            )

    def authenticate_header(self, request):
        return self.keyword
