from .base import *

DEBUG = False

SWITCHBOARD_TEST_APP = None
HOST_TO_APP = {
    'penncoursealert.com': 'pca',
    'www.penncoursealert.com': 'pca',
    'penncourseplan.com': 'pcp',
    'www.penncourseplan.com': 'pcp',
    'penncoursereview.com': 'pcr',
    'www.penncoursereview.com': 'pcr'
}

if len(ALLOWED_HOSTS) == 0:
    ALLOWED_HOSTS = HOST_TO_APP.keys()
