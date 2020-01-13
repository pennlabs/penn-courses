import os
from .base import *


PCA_URL = 'http://localhost:8000'
SENTRY_KEY = ''

'''
Custom Switchboard Middleware (docker should fix this)

This is the app that you want to run locally. While all Penn Courses apps run off the same django backend,
they operate with different URL schemes since they have different APIs. The app value should correspond to a file
in PennCourses/urls/. `pca` and `pcp` are two examples.
'''
SWITCHBOARD_TEST_APP = os.environ.get('DEVELOPMENT_APP', 'pcp').lower()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
PLATFORM_ACCOUNTS.update(
    {
        'REDIRECT_URI': os.environ.get('LABS_REDIRECT_URI', 'http://localhost:8000/accounts/callback/'),
        'CLIENT_ID': 'clientid',
        'CLIENT_SECRET': 'supersecretclientsecret',
        'PLATFORM_URL': 'https://platform-dev.pennlabs.org',
        'CUSTOM_ADMIN': False,
    }
)
