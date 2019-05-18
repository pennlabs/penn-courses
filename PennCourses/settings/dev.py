from .base import *

BASE_URL = 'http://localhost:8000'
SENTRY_KEY = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
