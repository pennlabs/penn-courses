import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *


DEBUG = False

sentry_sdk.init(
    dsn='https://a8da22bb171b439b9a8a8d7fb974d840:a9d22ba68b2644c6ac1a3b325f5cd13a@sentry.pennlabs.org/14',
    integrations=[DjangoIntegration(), CeleryIntegration()]
)

# Whitenoise Configuration
MIDDLEWARE.remove('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.remove('PennCourses.middleware.SwitchboardMiddleware')
MIDDLEWARE.remove('corsheaders.middleware.CorsMiddleware')
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'PennCourses.middleware.SwitchboardMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Share cookie with frontend
SESSION_COOKIE_DOMAIN = '.pennlabs.org'
CSRF_COOKIE_DOMAIN = '.pennlabs.org'
CSRF_COOKIE_SAMESITE = None

# Django CORS Settings
CORS_ORIGIN_REGEX_WHITELIST = [
    r'^https://[\w-]+.penncourseplan.com$',
    r'^https://penncourseplan.com$'
]

CSRF_TRUSTED_ORIGINS = [
    '.penncourseplan.com',
    'penncourseplan.com',
    '.penncoursealert.com',
    'penncoursealert.com',
]

# Domain Routing Middleware
# Define URL schemes for each domain.
SWITCHBOARD_TEST_APP = None
HOST_TO_APP = {
    'penncourses.apps.pennlabs.org': 'pca',
    'penncoursealert.com': 'pca',
    'www.penncoursealert.com': 'pca',

    'penncourseplan.com': 'pcp',
    'www.penncourseplan.com': 'pcp',
    'penncoursesearch.com': 'pcp-construction',
    'www.penncoursesearch.com': 'pcp-construction',

    'api.penncourses.org': 'api',
}

if len(ALLOWED_HOSTS) == 0:
    ALLOWED_HOSTS = HOST_TO_APP.keys()

# TODO: This is a BAD HACK. We shouldn't hardcode the base URL into the shortener
PCA_URL = 'https://penncoursealert.com'
