from .base import *

BASE_URL = 'http://localhost:8000'
SENTRY_KEY = ''

'''
Custom Switchboard Middleware

This is the app that you want to run locally. While all Penn Courses apps run off the same django backend,
they operate with different URL schemes since they have different APIs. The app value should correspond to a file
in PennCourses/urls/. `pca` and `pcp` are two examples.
'''
SWITCHBOARD_TEST_APP = 'pcp'
