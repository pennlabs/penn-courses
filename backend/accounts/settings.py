import os

from django.conf import settings


USER_SETTINGS = getattr(settings, "PLATFORM_ACCOUNTS", {})

DEFAULTS = {
    "CLIENT_ID": os.environ.get("LABS_CLIENT_ID"),
    "CLIENT_SECRET": os.environ.get("LABS_CLIENT_SECRET"),
    "REDIRECT_URI": os.environ.get("LABS_REDIRECT_URI"),
    "SCOPE": ["read", "introspection"],
    "PLATFORM_URL": "https://platform.pennlabs.org",
    "ADMIN_PERMISSION": "example_admin",
    "CUSTOM_ADMIN": True,
}


class AccountsSettings(object):
    """
    Based on https://github.com/encode/django-rest-framework/blob/master/rest_framework/settings.py
    """

    def __init__(self, settings=None, defaults=None):
        self.settings = settings or {}
        self.defaults = defaults or {}

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError("Invalid Penn Labs accounts setting: %s" % attr)

        try:
            val = self.settings[attr]
        except KeyError:
            val = self.defaults[attr]

        setattr(self, attr, val)
        return val


accounts_settings = AccountsSettings(USER_SETTINGS, DEFAULTS)
