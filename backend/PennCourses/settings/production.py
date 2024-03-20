import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from PennCourses.settings.base import *  # noqa: F401, F403


DEBUG = False

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow production host headers
ALLOWED_HOSTS = DOMAINS

# Sentry settings
SENTRY_URL = os.environ.get("SENTRY_URL", "")
sentry_sdk.init(dsn=SENTRY_URL, integrations=[CeleryIntegration(), DjangoIntegration()])

# DLA settings
PLATFORM_ACCOUNTS = {"ADMIN_PERMISSION": "penn_courses_admin"}

# TODO: This is a BAD HACK. We shouldn't hardcode the base URL into the shortener
PCA_URL = "https://penncoursealert.com"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # ignore Redis connection errors
            "SOCKET_CONNECT_TIMEOUT": 1,
            "SOCKET_TIMEOUT": 1,
        },
    }
}

MOBILE_NOTIFICATION_SECRET = os.environ.get("MOBILE_NOTIFICATION_SECRET", "")
