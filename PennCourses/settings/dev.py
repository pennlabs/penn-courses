from .base import *


PCA_URL = 'http://localhost:8000'
SENTRY_KEY = ''

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
