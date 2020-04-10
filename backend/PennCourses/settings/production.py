import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from PennCourses.settings.base import *  # noqa: F401, F403
from PennCourses.settings.base import DATABASES


DEBUG = False

# Fix MySQL Emoji support
DATABASES["default"]["OPTIONS"] = {"charset": "utf8mb4"}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow production host headers
ALLOWED_HOSTS = ["penncourseplan.com", "beta.penncoursealert.com", "penncoursealert.com"]

# Make sure SECRET_KEY is set to a secret in production
# SECRET_KEY = os.environ.get("SECRET_KEY", None)  # TODO: remove after testing

# Sentry settings
SENTRY_URL = os.environ.get("SENTRY_URL", "")
sentry_sdk.init(dsn=SENTRY_URL, integrations=[CeleryIntegration(), DjangoIntegration()])

# DLA settings
PLATFORM_ACCOUNTS = {"ADMIN_PERMISSION": "courses_admin"}

# TODO: This is a BAD HACK. We shouldn't hardcode the base URL into the shortener
PCA_URL = "https://penncoursealert.com"
