from datetime import timedelta

import requests
from django.utils import timezone

from accounts.settings import accounts_settings


# IPC on behalf of a user for when a user in a product wants to use an
# authenticated route on another product.
def authenticated_request(
    user,
    method,
    url,
    params=None,
    data=None,
    headers=None,
    cookies=None,
    files=None,
    auth=None,
    timeout=None,
    allow_redirects=True,
    proxies=None,
    hooks=None,
    stream=None,
    verify=None,
    cert=None,
    json=None,
):
    """
    Helper method to make an authenticated request using the user's access token
    NOTE be ABSOLUTELY sure you only make a request to Penn Labs products, otherwise
    you will expose user's access tokens to the URL you provide and bad things will
    happen
    """

    # Access token is expired. Try to refresh access token
    if user.accesstoken.expires_at < timezone.now():
        if not _refresh_access_token(user):
            # Couldn't update the user's access token. Return a response with a 403 status code
            # as if the user didn't have access to the requested resource
            response = requests.models.Response
            response.status_code = 403
            return response

    # Update Headers
    headers = {} if headers is None else headers
    headers["Authorization"] = f"Bearer {user.accesstoken.token}"

    # Make the request
    # We're only using a session to provide an easy wrapper to define the http method
    # GET, POST, etc in the method call.
    s = requests.Session()
    return s.request(
        method=method,
        url=url,
        params=params,
        data=data,
        headers=headers,
        cookies=cookies,
        files=files,
        auth=None,
        timeout=None,
        allow_redirects=allow_redirects,
        proxies=proxies,
        hooks=hooks,
        stream=stream,
        verify=verify,
        cert=cert,
        json=json,
    )


def _refresh_access_token(user):
    """
    Helper method to update a user's access token. Should be used when a user's
    access token has expired, but still has a valid refresh token.

    Returns:
        bool: true if the access token is updated, false otherwise.
    """
    body = {
        "grant_type": "refresh_token",
        "client_id": accounts_settings.CLIENT_ID,  # from Product
        "client_secret": accounts_settings.CLIENT_SECRET,  # from Product
        "refresh_token": user.refreshtoken.token,  # refresh token from user
    }
    try:
        data = requests.post(
            url=accounts_settings.PLATFORM_URL + "/accounts/token/", data=body
        )
        if data.status_code == 200:  # Access token refreshed successfully
            data = data.json()
            # Update Access token
            user.accesstoken.token = data["access_token"]
            user.accesstoken.expires_at = timezone.now() + timedelta(
                seconds=data["expires_in"]
            )
            user.accesstoken.save()

            # Update Refresh Token
            user.refreshtoken.token = data["refresh_token"]
            user.refreshtoken.save()

            return True
    except requests.exceptions.RequestException:  # Can't connect to platform
        return False
    return False
