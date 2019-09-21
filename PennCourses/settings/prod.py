from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

DEBUG = False

SWITCHBOARD_TEST_APP = None
HOST_TO_APP = {
    'penncoursealert.com': 'pca',
    'www.penncoursealert.com': 'pca',
    'penncourseplan.com': 'pcp',
    'www.penncourseplan.com': 'pcp',
    'penncoursereview.com': 'pcr',
    'www.penncoursereview.com': 'pcr'
}

if len(ALLOWED_HOSTS) == 0:
    ALLOWED_HOSTS = HOST_TO_APP.keys()

sentry_sdk.init(
    dsn='https://a8da22bb171b439b9a8a8d7fb974d840:a9d22ba68b2644c6ac1a3b325f5cd13a@sentry.pennlabs.org/14',
    integrations=[DjangoIntegration(), CeleryIntegration()]
)

