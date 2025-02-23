from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from courses.models import Friendship, UserProfile


class FriendshipModelTest(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )
        self.u2 = User.objects.create_user(
            username="test2", password="top_secret_pass", email="test2@example.com"
        )

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.login(username="test", password="top_secret")
        self.client2.login(username="test2", password="top_secret_pass")

    def test_basic_friendship(self):
        u1 = self.u1
        u2 = self.u2

        self.assertTrue(UserProfile.objects.filter(user=u2).exists())
        self.assertTrue(UserProfile.objects.filter(user=u1).exists())

        make_friends = self.client1.post(reverse("friendship"), {"pennkey": u2.username.upper()})

        self.assertEquals(make_friends.status_code, 201)
        self.assertTrue(
            Friendship.objects.filter(
                sender=u1, recipient=u2, status=Friendship.Status.SENT
            ).exists()
        )
        self.assertFalse(Friendship.objects.filter(sender=u2, recipient=u1).exists())

    def test_none_username(self):
        u1 = self.u1
        u2 = self.u2

        self.assertTrue(UserProfile.objects.filter(user=u2).exists())
        self.assertTrue(UserProfile.objects.filter(user=u1).exists())

        make_friends = self.client1.post(reverse("friendship"), {"pennkey": ""})

        self.assertEquals(make_friends.status_code, 404)

    def test_none_delete(self):
        u1 = self.u1
        u2 = self.u2

        self.assertTrue(UserProfile.objects.filter(user=u2).exists())
        self.assertTrue(UserProfile.objects.filter(user=u1).exists())

        make_friends = self.client1.post(reverse("friendship"), {"pennkey": u2.username.upper()})
        self.assertEquals(make_friends.status_code, 201)

        delete_none = self.client1.delete(reverse("friendship"), {"pennkey": ""})
        self.assertEquals(delete_none.status_code, 404)

        delete_friends = self.client2.delete(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(delete_friends.status_code, 200)

    def test_basic_friendship_accept(self):
        u1 = self.u1
        u2 = self.u2

        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 201)

        make_friends2 = self.client1.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends2.status_code, 200)

        self.assertTrue(
            Friendship.objects.filter(
                sender=u2, recipient=u1, status=Friendship.Status.ACCEPTED
            ).exists()
        )
        self.assertFalse(
            Friendship.objects.filter(
                sender=u2, recipient=u1, status=Friendship.Status.SENT
            ).exists()
        )

    def test_basic_friendship_reject(self):
        u1 = self.u1
        u2 = self.u2
        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 201)
        make_friends2 = self.client1.delete(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends2.status_code, 200)

        self.assertTrue(
            Friendship.objects.filter(
                sender=u2, recipient=u1, status=Friendship.Status.REJECTED
            ).exists()
        )
        self.assertFalse(
            Friendship.objects.filter(
                sender=u2, recipient=u1, status=Friendship.Status.SENT
            ).exists()
        )

    def test_basic_friendship_delete_request(self):
        u1 = self.u1
        u2 = self.u2
        friendship = Friendship(sender=u1, recipient=u2, status=Friendship.Status.SENT)
        friendship.save()

        remove_friend = self.client1.delete(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(remove_friend.status_code, 200)  # delete friendship request

        self.assertFalse(Friendship.objects.filter(sender=u2, recipient=u1).exists())

    def test_basic_friendship_remove(self):
        u1 = self.u1
        u2 = self.u2
        friendship = Friendship(sender=u2, recipient=u1, status=Friendship.Status.ACCEPTED)
        friendship.save()

        make_friends2 = self.client2.delete(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends2.status_code, 200)  # remove friend

        self.assertFalse(Friendship.objects.filter(sender=u2, recipient=u1).exists())

    def test_basic_null_delete(self):
        u1 = self.u1
        make_friends = self.client2.delete(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 404)  # friendship does not exist

    def test_duplicate_accepts(self):
        u1 = self.u1
        u2 = self.u2
        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 201)

        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 409)  # duplicate friendship request

        make_friends2 = self.client1.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends2.status_code, 200)  # accepted friend request

        make_friends2 = self.client1.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends2.status_code, 409)  # duplicate accepted friendship

    def test_duplicate_rejects(self):
        u1 = self.u1
        u2 = self.u2
        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 201)

        make_friends = self.client1.delete(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends.status_code, 200)  # reject friendship request

        make_friends = self.client1.delete(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends.status_code, 409)  # already rejected friendship request

    def test_friendship_after_rejection(self):
        u1 = self.u1
        u2 = self.u2
        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 201)
        make_friends2 = self.client1.delete(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends2.status_code, 200)

        self.assertTrue(
            Friendship.objects.filter(
                sender=u2, recipient=u1, status=Friendship.Status.REJECTED
            ).exists()
        )

        make_friends3 = self.client1.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends3.status_code, 200)
        self.assertFalse(
            Friendship.objects.filter(sender=u2, recipient=u1).exists()
        )  # request from other user should change the entry
        self.assertTrue(
            Friendship.objects.filter(sender=u1, recipient=u2).exists()
        )  # row should be changed to this from the request

    def test_get_friendship_multiple(self):
        # TODO: add functions to test the following friendship logic:
        u1 = self.u1
        u2 = self.u2
        u3 = User.objects.create_user(
            username="test3", password="top_secret_pass", email="test3@example.com"
        )
        u4 = User.objects.create_user(
            username="test4", password="top_secret_pass", email="test4@example.com"
        )
        self.client3 = APIClient()
        self.client4 = APIClient()
        self.client3.login(username="test3", password="top_secret_pass")
        self.client4.login(username="test4", password="top_secret_pass")

        make_friends = self.client1.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends.status_code, 201)
        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u1.username})
        self.assertEquals(make_friends.status_code, 200)

        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u3.username})
        self.assertEquals(make_friends.status_code, 201)
        make_friends = self.client3.post(reverse("friendship"), {"pennkey": u2.username})
        self.assertEquals(make_friends.status_code, 200)

        make_friends = self.client2.post(reverse("friendship"), {"pennkey": u4.username})
        self.assertEquals(make_friends.status_code, 201)

        get_friends = self.client2.get(reverse("friendship"))
        self.assertEquals(get_friends.status_code, 200)
