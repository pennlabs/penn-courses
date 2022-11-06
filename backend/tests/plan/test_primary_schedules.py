from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from courses.models import UserProfile
from options.models import Option
from rest_framework.test import APIClient

from alert.management.commands.recomputestats import recompute_precomputed_fields
from alert.models import AddDropPeriod
from courses.models import Friendship
from tests.courses.util import create_mock_data

class PrimaryScheduleTest(TestCase):
    
    def setUp(self):
        # TODO: write test cases for the following cases
        '''
            - retrieve primary schedule and update it with a valid schedule (check to see if old is not primary anymore)
            - remove primary schedule (and check no other primary scheudles in the models)
            - retrieve all friends schedules (and verify that they are primary)
            - retrieve specific friend's primary schedule
            - removing friend does not retrieve their primary schedule
        '''

