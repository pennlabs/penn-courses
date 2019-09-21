from .base import *
SENTRY_KEY = ''
SWITCHBOARD_TEST_APP = None
PCA_URL = 'http://localhost:8000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite3',
    }
}
