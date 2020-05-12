"""
Django settings for PennCourses project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import dj_database_url


DOMAIN = os.environ.get("DOMAIN", "example.com")

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "&3!f%)t!o$+dwu3(jao7ipi2f4(k-2ua7@28+^yge-cn7c!_14")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "debug_toolbar",
    "corsheaders",
    "shortener.apps.ShortenerConfig",
    "accounts.apps.AccountsConfig",
    "options.apps.OptionsConfig",
    "alert",
    "courses",
    "plan",
    "review",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 'accounts.middleware.OAuth2TokenMiddleware',
]

ROOT_URLCONF = os.environ.get("ROOT_URLCONF", "PennCourses.urls.api")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["PennCourses/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "PennCourses.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(default="sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3"))
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Authentication Backends

AUTHENTICATION_BACKENDS = [
    "accounts.backends.LabsUserBackend",
    "django.contrib.auth.backends.ModelBackend",
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/assets/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


# DLA Settings

PLATFORM_ACCOUNTS = {
    "REDIRECT_URI": os.environ.get("LABS_REDIRECT_URI", "http://localhost:8000/accounts/callback/"),
    "CLIENT_ID": "clientid",
    "CLIENT_SECRET": "supersecretclientsecret",
    "PLATFORM_URL": "https://platform-dev.pennlabs.org",
    "CUSTOM_ADMIN": False,
}


# Penn OpenData API
API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")
API_URL = "https://esb.isc-seo.upenn.edu/8091/open_data/course_section_search"

# Penn OpenData Course Status Webhook Auth
WEBHOOK_USERNAME = os.environ.get("WEBHOOK_USERNAME", "webhook")
WEBHOOK_PASSWORD = os.environ.get("WEBHOOK_PASSWORD", "password")

# Email Configuration
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = os.environ.get("SMTP_PORT", 587)
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Twilio Credentials
TWILIO_SID = os.environ.get("TWILIO_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN", "")
TWILIO_NUMBER = os.environ.get("TWILIO_NUMBER", "+12153984277")

# Penn Course Review API
PCR_TOKEN = os.environ.get("PCR_TOKEN", "")

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost")

# Celery
MESSAGE_BROKER_URL = REDIS_URL

# Django REST Framework
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
}

# Django Debug Toolbar
INTERNAL_IPS = ["127.0.0.1"]
