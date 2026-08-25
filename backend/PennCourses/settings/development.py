import os

from PennCourses.settings.base import *  # noqa: F401, F403


PCA_URL = "http://localhost:8000"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1"]

# One entry per frontend dev server. Django checks the browser's Origin header
# against this list on every POST, so an app on an untrusted port gets a 403.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",  # penncourseplan, penncoursealert, penncoursereview
    "http://localhost:3001",  # penncoursechat
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
