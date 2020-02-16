import os

from PennCourses.settings.base import *  # noqa: F401, F403


PCA_URL = "http://localhost:8000"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
