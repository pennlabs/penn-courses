import os
from .base import *


PCA_URL = 'http://localhost:8000'
SENTRY_KEY = ''

ROOT_URLCONF = os.environ.get('ROOT_URLCONF', 'PennCourses.urls.api')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}
