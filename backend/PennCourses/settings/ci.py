from PennCourses.settings.base import *  # noqa: F401, F403


PCA_URL = "http://localhost:8000"

TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_VERBOSE = 2
TEST_OUTPUT_DIR = "test-results"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
