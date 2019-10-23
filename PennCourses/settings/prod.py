import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from PennCourses.settings.base import *


DEBUG = False

sentry_sdk.init(
    dsn='https://a8da22bb171b439b9a8a8d7fb974d840:a9d22ba68b2644c6ac1a3b325f5cd13a@sentry.pennlabs.org/14',
    integrations=[DjangoIntegration(), CeleryIntegration()]
)

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ROOT_URLCONF = os.environ.get('ROOT_URLCONF', None)

ALLOWED_HOSTS = [
    'api.penncourses.org'
    'penncoursealert.com'
    'www.penncoursealert.com'
]

# TODO: This is a BAD HACK. We shouldn't hardcode the base URL into the shortener
PCA_URL = 'https://penncoursealert.com'
