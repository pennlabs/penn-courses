from PennCourses.settings.base import *


SENTRY_KEY = ""
SWITCHBOARD_TEST_APP = None
PCA_URL = "http://localhost:8000"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "test.sqlite3",}}


TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_VERBOSE = 2
TEST_OUTPUT_DIR = "test-results"
