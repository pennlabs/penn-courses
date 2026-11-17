from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from degree.models import PDPBetaReferral, PDPBetaUser
from degree.tasks import send_referral_email


Status = PDPBetaUser.Status
Referral = PDPBetaReferral.Status
users = get_user_model().objects


class MockedEmailTestCase(TestCase):
    def setUp(self):
        delay = patch("degree.tasks.send_referral_email.delay")
        self.delay = delay.start()
        self.addCleanup(delay.stop)


class InviteTest(MockedEmailTestCase):
    def setUp(self):
        super().setUp()
        self.user = users.create_user(username="s", password="x", first_name="Sam")
        PDPBetaUser.objects.create(person=self.user, status=Status.APPROVED)
        self.client = APIClient()
        self.client.force_login(self.user)

    def invite(self, *friends):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                reverse("beta-invites"), {"friends": list(friends)}, format="json"
            )

    def test_inviting_records_pending_referrals_without_emailing(self):
        response = self.invite("alice", " Bob ")

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i["pennkey"] for i in response.data["invites"]], ["alice", "bob"])
        self.assertEqual({i["status"] for i in response.data["invites"]}, {Referral.PENDING})
        self.assertEqual(response.data["remaining"], 1)
        self.delay.assert_not_called()

    def test_an_invite_does_not_grant_access(self):
        self.invite("alice")
        alice = users.create_user(username="alice", password="x")
        self.client.force_login(alice)
        self.assertEqual(self.client.get(reverse("onboarding-status")).status_code, 403)

    def test_at_most_three_friends(self):
        self.invite("amy", "ben")
        response = self.invite("cat", "dan")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(PDPBetaReferral.objects.count(), 2)
        self.assertEqual(self.invite("cat").status_code, 201)
        self.assertEqual(self.invite("dan").status_code, 400)

    def test_inviting_someone_twice_is_one_invite(self):
        self.invite("alice")
        self.invite("alice", "ALICE")
        self.assertEqual(PDPBetaReferral.objects.count(), 1)

    def test_only_pennkeys(self):
        self.assertEqual(self.invite("alice@upenn.edu").status_code, 400)
        self.assertEqual(self.invite("al ice").status_code, 400)
        self.assertFalse(PDPBetaReferral.objects.exists())

    def test_not_yourself(self):
        self.assertEqual(self.invite("S").status_code, 400)

    def test_only_beta_users_can_invite(self):
        self.user.pdp_beta.decide(Status.DENIED)
        self.assertEqual(self.invite("alice").status_code, 403)
        self.assertEqual(self.client.get(reverse("beta-invites")).status_code, 403)


class ApprovingReferralsTest(MockedEmailTestCase):
    def setUp(self):
        super().setUp()
        self.referrer = users.create_user(username="s")
        self.referral = PDPBetaReferral.objects.create(referrer=self.referrer, pennkey="alice")

    def approve(self, referral=None):
        with self.captureOnCommitCallbacks(execute=True):
            (referral or self.referral).decide(Referral.APPROVED)

    def can_use_pdp(self, person):
        client = APIClient()
        client.force_login(person)
        return client.get(reverse("onboarding-status")).status_code == 200

    def test_approving_emails_the_friend_once(self):
        self.approve()
        self.delay.assert_called_once_with(self.referral.id)

    def test_denying_sends_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.referral.decide(Referral.DENIED)
        self.delay.assert_not_called()

    def test_a_friend_who_never_logged_in_is_let_in_on_first_login(self):
        self.approve()
        alice = users.create_user(username="alice")

        self.assertTrue(self.can_use_pdp(alice))
        beta = PDPBetaUser.objects.get(person=alice)
        self.assertEqual(beta.status, Status.APPROVED)
        self.assertIsNotNone(beta.notified_at)  # so no second "you're in" email

    def test_an_existing_user_is_let_in_right_away(self):
        alice = users.create_user(username="alice")
        PDPBetaUser.objects.create(person=alice, status=Status.REQUESTED)

        self.approve()

        beta = PDPBetaUser.objects.get(person=alice)
        self.assertEqual(beta.status, Status.APPROVED)
        self.assertIsNotNone(beta.notified_at)
        self.delay.assert_called_once()

    def test_someone_already_in_is_not_emailed(self):
        alice = users.create_user(username="alice")
        PDPBetaUser.objects.create(person=alice, status=Status.APPROVED)
        self.approve()
        self.delay.assert_not_called()

    def test_a_revoke_after_redeeming_stands(self):
        self.approve()
        alice = users.create_user(username="alice")
        self.assertTrue(self.can_use_pdp(alice))

        alice.pdp_beta.decide(Status.DENIED)

        self.assertFalse(self.can_use_pdp(alice))

    def test_a_pending_referral_lets_no_one_in(self):
        alice = users.create_user(username="alice")
        self.assertFalse(self.can_use_pdp(alice))
        self.assertFalse(PDPBetaUser.objects.filter(person=alice).exists())

    def test_one_approval_answers_everyone_who_invited_the_friend(self):
        other = PDPBetaReferral.objects.create(
            referrer=users.create_user(username="t"), pennkey="alice"
        )
        self.approve()

        other.refresh_from_db()
        self.assertEqual(other.status, Referral.APPROVED)
        self.delay.assert_called_once()


class ReferralDashboardTest(MockedEmailTestCase):
    def setUp(self):
        super().setUp()
        self.staff = users.create_user(username="staff", password="x", is_staff=True)
        self.referrer = users.create_user(username="s", first_name="Sam", last_name="Lee")
        self.alice = PDPBetaReferral.objects.create(referrer=self.referrer, pennkey="alice")
        PDPBetaReferral.objects.create(referrer=self.referrer, pennkey="bob")
        self.client = APIClient()
        self.client.force_login(self.staff)

    def test_only_staff(self):
        self.client.force_login(self.referrer)
        self.assertEqual(self.client.get(reverse("beta-referral-list")).status_code, 403)

    def test_lists_referrals_with_the_friends_requests(self):
        alice = users.create_user(username="alice")
        PDPBetaUser.objects.create(person=alice, status=Status.REQUESTED)

        data = {r["pennkey"]: r for r in self.client.get(reverse("beta-referral-list")).data}

        self.assertEqual(data["alice"]["referrer_name"], "Sam Lee")
        self.assertEqual(data["alice"]["status"], Referral.PENDING)
        self.assertEqual(data["alice"]["invitee"]["status"], Status.REQUESTED)
        self.assertIsNone(data["bob"]["invitee"])

    def test_approving_from_the_dashboard(self):
        url = reverse("beta-referral-detail", args=[self.alice.id])
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.patch(url, {"status": Referral.APPROVED}, format="json")

        self.assertEqual(response.status_code, 200)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.status, Referral.APPROVED)
        self.delay.assert_called_once_with(self.alice.id)

    def test_beta_requests_say_who_referred_them(self):
        alice = users.create_user(username="alice")
        PDPBetaUser.objects.create(person=alice, status=Status.REQUESTED)

        data = self.client.get(reverse("beta-request-list")).data

        self.assertEqual(data[0]["referred_by"], ["s"])


@override_settings(SMTP_HOST="smtp.example.com", PDP_URL="https://pdp.example")
class ReferralEmailTaskTest(TestCase):
    def setUp(self):
        referrer = users.create_user(username="s", first_name="Sam", last_name="Lee")
        self.referral = PDPBetaReferral.objects.create(
            referrer=referrer, pennkey="alice", status=Referral.APPROVED
        )

    @patch("degree.tasks.send_email")
    def test_sends_once_without_naming_the_referrer(self, send_email):
        self.assertEqual(send_referral_email(self.referral.id)["result"], "sent")
        self.assertEqual(send_referral_email(self.referral.id)["result"], "skipped")

        send_email.assert_called_once()
        kwargs = send_email.call_args.kwargs
        self.assertEqual(kwargs["to"], "alice@upenn.edu")
        self.assertEqual(kwargs["subject"], "A friend invited you to try Penn Degree Plan")
        self.assertNotIn("Sam", kwargs["html"])
        self.assertNotIn("Lee", kwargs["html"])

    @patch("degree.tasks.send_email")
    def test_a_pending_referral_is_not_emailed(self, send_email):
        self.referral.status = Referral.PENDING
        self.referral.save()
        self.assertEqual(send_referral_email(self.referral.id)["result"], "skipped")
        send_email.assert_not_called()

    @patch("degree.tasks.send_email")
    def test_a_friend_invited_twice_hears_once(self, send_email):
        other = PDPBetaReferral.objects.create(
            referrer=users.create_user(username="t"), pennkey="alice", status=Referral.APPROVED
        )
        send_referral_email(self.referral.id)
        self.assertEqual(send_referral_email(other.id)["result"], "skipped")
        send_email.assert_called_once()

    @override_settings(SMTP_HOST="")
    @patch("degree.tasks.send_email")
    def test_does_nothing_without_smtp(self, send_email):
        self.assertEqual(send_referral_email(self.referral.id)["result"], "not configured")
        send_email.assert_not_called()
