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

class FriendshipModelTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )
        self.u2 = User.objects.create_user(
            username="test2", password="top_secret_pass", email="test2@example.com"
        )
    

    def test_basic_friendship(self):
        u1 = self.u1
        u2 = self.u2

        self.assertTrue(UserProfile.objects.filter(user=u2).exists())
        self.assertTrue(UserProfile.objects.filter(user=u1).exists())

        friendship = Friendship(sender=u1, recipient=u2)
        friendship.save()
        print(friendship)
        obj = Friendship.objects.first()
        print(obj)
        self.assertEquals(friendship.status, Friendship.Status.SENT)
        self.assertTrue(Friendship.objects.filter(sender=u1, recipient=u2).exists())
        self.assertFalse(Friendship.objects.filter(sender=u2, recipient=u1).exists())
    
    def test_basic_friendship_accept(self):
        u1 = self.u1
        u2 = self.u2
        friendship = Friendship(sender=u1, recipient=u2)
        friendship.save()

        self.assertEquals(friendship.status, Friendship.Status.SENT)
        friendship = Friendship.objects.get(sender=u1, recipient=u2)
        friendship.status = Friendship.Status.ACCEPTED
        friendship.save()
        self.assertTrue(Friendship.objects.filter(sender=u1, recipient=u2, status=Friendship.Status.ACCEPTED).exists())
        self.assertFalse(Friendship.objects.filter(sender=u1, recipient=u2, status=Friendship.Status.SENT).exists())
    
    def test_basic_friendship_reject(self):
        u1 = self.u1
        u2 = self.u2
        friendship = Friendship(sender=u1, recipient=u2)
        friendship.save()


        friendship = Friendship.objects.get(sender=u1, recipient=u2)
        friendship.status = Friendship.Status.REJECTED
        friendship.save()
        self.assertTrue(Friendship.objects.filter(sender=u1, recipient=u2, status=Friendship.Status.REJECTED).exists())
        self.assertFalse(Friendship.objects.filter(sender=u1, recipient=u2, status=Friendship.Status.SENT).exists())

    
    def test_friendship_route_logic(self):
        # TODO: add functions to test the following friendship logic:

        '''
            - multiple friendship requests doesn't create multiple rows
            - if already friends, any other friendship request does not create new entries
            - frinedship request in the other direction accepts the original request
            - friendship requests are possible after one removes a friend / rejects a friendship request.
            - get friends returns all friends (even after removing + adding new friends)
            - requesting/accepting/rejecting/etc. invalid user for friend request leads to an error
            - 
        '''



