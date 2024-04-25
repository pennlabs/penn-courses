"""
Django settings for PennCourses project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

import boto3
import dj_database_url


DOMAINS = os.environ.get("DOMAINS", "example.com").split(",")

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
    "corsheaders",
    "shortener.apps.ShortenerConfig",
    "accounts.apps.AccountsConfig",
    "options.apps.OptionsConfig",
    "django.contrib.admindocs",
    "django_extensions",
    "alert",
    "courses",
    "plan",
    "review",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = os.environ.get("ROOT_URLCONF", "PennCourses.urls")

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
    "default": dj_database_url.config(
        # this is overriden by the DATABASE_URL env var
        default="postgres://penn-courses:postgres@localhost:5432/postgres"
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
# Explicitly setting DEFAULT_AUTO_FIELD is necessary to silence warnings after Django 3.2
# We don't need the range of BigAutoField for auto fields so we can stick with the old behavior


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
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
OPEN_DATA_CLIENT_ID = os.environ.get("OPEN_DATA_CLIENT_ID", "")
OPEN_DATA_OIDC_SECRET = os.environ.get("OPEN_DATA_OIDC_SECRET", "")
OPEN_DATA_TOKEN_URL = (
    "https://sso.apps.k8s.upenn.edu/auth/realms/master/protocol/openid-connect/token"
)
OPEN_DATA_API_BASE = "https://3scale-public-prod-open-data.apps.k8s.upenn.edu/api"

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

# Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")

# Celery
MESSAGE_BROKER_URL = REDIS_URL

# Django REST Framework
REST_FRAMEWORK = {
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_SCHEMA_CLASS": "PennCourses.docs_settings.PcxAutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "accounts.authentication.PlatformAuthentication",
    ],
}

STATS_WEBHOOK = os.environ.get("STATS_WEBHOOK", None)

S3_client = boto3.client("s3")
S3_resource = boto3.resource("s3")

# NGSS course code crosswalk stored in S3
XWALK_S3_BUCKET = "penn.courses"
XWALK_SRC = "xwalk_csre_number.txt"

# The first semester that used Banner/NGSS for course data.
# This was when course codes changed from 3-digit to 4-digit.
# Note that the above crosswalk connects pre and post NGSS courses
FIRST_BANNER_SEM = "2022B"

# Registration Metrics Settings

STATUS_UPDATES_RECORDED_SINCE = "2019C"  # How far back does our valid Status Update data span?
PCA_REGISTRATIONS_RECORDED_SINCE = "2020A"  # How far back does our valid Registration data span?
WAITLIST_DEPARTMENT_CODES = []  # Which departments (referenced by code) have a waitlist system
# or require permits for registration during the add/drop period?
PRE_NGSS_PERMIT_REQ_RESTRICTION_CODES = [
    "PCG",
    "PAD",
    "PCW",
    "PCD",
    "PLC",
    "PIN",
    "PDP",
]  # Which pre-NGSS restriction codes indicate registration was handled by permit issuance?
ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES = (
    200  # Aim for at least 200 demand distribution estimates over the course of a semester
)

# The name of the schedule that is created/verified by Penn Mobile,
# containing the user's active course registrations from Path.
PATH_REGISTRATION_SCHEDULE_NAME = "Path Registration"
