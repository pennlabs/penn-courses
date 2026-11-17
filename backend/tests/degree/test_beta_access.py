from smtplib import SMTPRecipientsRefused
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from degree.admin import PDPBetaUserAdmin
from degree.models import PDPBetaReferral, PDPBetaUser
from degree.tasks import send_beta_approval_email


Status = PDPBetaUser.Status


@override_settings(PDP_BETA_REQUESTS_OPEN=True)
class BetaAccessTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="s", password="x")
        self.client = APIClient()
        self.client.force_login(self.user)

    def beta(self):
        return self.client.get(reverse("beta-access")).data["status"]

    def request_access(self):
        return self.client.post(reverse("beta-access"))

    def can_use_pdp(self):
        return self.client.get(reverse("onboarding-status")).status_code == 200

    def test_a_new_user_can_request_access(self):
        self.assertEqual(self.beta(), "NONE")

        response = self.request_access()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Status.REQUESTED)
        self.assertEqual(self.beta(), Status.REQUESTED)

    def test_a_request_does_not_let_the_user_in(self):
        self.request_access()

        response = self.client.get(reverse("onboarding-status"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Not in the PDP beta.")

    def test_an_approved_user_gets_in(self):
        PDPBetaUser.objects.create(person=self.user, status=Status.APPROVED)
        self.assertTrue(self.can_use_pdp())
        self.assertEqual(self.beta(), Status.APPROVED)

    def test_a_row_added_by_an_admin_is_a_grant(self):
        PDPBetaUser.objects.create(person=self.user)
        self.assertTrue(self.can_use_pdp())

    def test_asking_again_changes_nothing(self):
        PDPBetaUser.objects.create(person=self.user, status=Status.DENIED)

        response = self.request_access()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Status.DENIED)
        self.assertEqual(PDPBetaUser.objects.filter(person=self.user).count(), 1)
        self.assertFalse(self.can_use_pdp())

    def test_logged_out_users_cannot_request(self):
        self.client.logout()
        self.assertIn(self.request_access().status_code, (401, 403))
        self.assertFalse(PDPBetaUser.objects.exists())


@override_settings(PDP_BETA_REQUESTS_OPEN=False)
class InviteOnlyBetaAccessTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="s", password="x")
        self.client = APIClient()
        self.client.force_login(self.user)

    def test_says_requests_are_closed(self):
        response = self.client.get(reverse("beta-access"))
        self.assertEqual(response.data, {"status": "NONE", "requests_open": False})

    def test_a_new_user_cannot_request_access(self):
        response = self.client.post(reverse("beta-access"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Penn Degree Plan is invite-only right now.")
        self.assertFalse(PDPBetaUser.objects.exists())

    def test_an_existing_request_is_left_alone(self):
        PDPBetaUser.objects.create(person=self.user, status=Status.REQUESTED)

        response = self.client.post(reverse("beta-access"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], Status.REQUESTED)
        self.assertEqual(PDPBetaUser.objects.get().status, Status.REQUESTED)

    def test_a_friends_invite_still_lets_a_new_user_in(self):
        friend = get_user_model().objects.create_user(username="f", password="x")
        PDPBetaReferral.objects.create(
            referrer=friend, pennkey="s", status=PDPBetaReferral.Status.APPROVED
        )

        response = self.client.get(reverse("beta-access"))
        self.assertEqual(response.data["status"], Status.APPROVED)
        self.assertEqual(self.client.get(reverse("onboarding-status")).status_code, 200)

    def test_invited_users_still_get_in(self):
        PDPBetaUser.objects.create(person=self.user, status=Status.APPROVED)
        self.assertEqual(self.client.get(reverse("onboarding-status")).status_code, 200)


class BetaAccessAdminTest(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.admin_user = users.create_superuser(username="admin", password="x")
        self.pending = PDPBetaUser.objects.create(
            person=users.create_user(username="pending"), status=Status.REQUESTED
        )
        self.member = PDPBetaUser.objects.create(person=users.create_user(username="member"))
        self.model_admin = PDPBetaUserAdmin(PDPBetaUser, AdminSite())

    def admin_request(self):
        request = RequestFactory().get("/")
        request.user = self.admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_pending_requests_come_first(self):
        rows = list(self.model_admin.get_queryset(self.admin_request()))
        self.assertEqual(rows[0], self.pending)

    def test_approving_lets_a_user_in_and_records_when(self):
        self.model_admin.approve(
            self.admin_request(), PDPBetaUser.objects.filter(pk=self.pending.pk)
        )

        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Status.APPROVED)
        self.assertIsNotNone(self.pending.decided_at)

    def test_denying_records_when(self):
        self.model_admin.deny(self.admin_request(), PDPBetaUser.objects.filter(pk=self.pending.pk))

        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Status.DENIED)
        self.assertIsNotNone(self.pending.decided_at)

    def test_the_admin_list_page_loads(self):
        client = APIClient()
        client.force_login(self.admin_user)
        response = client.get(reverse("admin:degree_pdpbetauser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pending")


class BetaRequestApiTest(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.staff = users.create_user(username="staff", password="x", is_staff=True)
        self.member = PDPBetaUser.objects.create(person=users.create_user(username="member"))
        self.pending = PDPBetaUser.objects.create(
            person=users.create_user(username="pending", email="p@upenn.edu"),
            status=Status.REQUESTED,
        )
        users.create_user(username="newcomer")
        self.client = APIClient()
        self.client.force_login(self.staff)

    def detail(self, beta):
        return reverse("beta-request-detail", kwargs={"pk": beta.pk})

    def test_only_staff_can_use_it(self):
        student = get_user_model().objects.create_user(username="student")
        self.client.force_login(student)
        self.assertEqual(self.client.get(reverse("beta-request-list")).status_code, 403)
        response = self.client.patch(self.detail(self.pending), {"status": "APPROVED"})
        self.assertEqual(response.status_code, 403)

    def test_lists_pending_requests_first(self):
        response = self.client.get(reverse("beta-request-list"))
        self.assertEqual([row["username"] for row in response.data], ["pending", "member"])
        self.assertEqual(response.data[0]["email"], "p@upenn.edu")

    def test_filters_by_status(self):
        response = self.client.get(reverse("beta-request-list"), {"status": "REQUESTED"})
        self.assertEqual([row["username"] for row in response.data], ["pending"])

    def test_approving_a_request_lets_the_user_in(self):
        response = self.client.patch(self.detail(self.pending), {"status": "APPROVED"})

        self.assertEqual(response.status_code, 200, response.data)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Status.APPROVED)
        self.assertIsNotNone(self.pending.decided_at)

    def test_granting_access_by_pennkey(self):
        response = self.client.post(reverse("beta-request-list"), {"username": "newcomer"})

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], Status.APPROVED)
        self.assertTrue(
            PDPBetaUser.objects.filter(person__username="newcomer", status=Status.APPROVED).exists()
        )

    def test_granting_an_unknown_pennkey_fails(self):
        response = self.client.post(reverse("beta-request-list"), {"username": "nobody"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.data)

    def test_the_user_endpoint_says_who_is_staff(self):
        response = self.client.get(reverse("user-view"))
        self.assertTrue(response.data["is_staff"])


QUEUE = "degree.tasks.send_beta_approval_email.delay"


class ApprovalEmailQueuedTest(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.staff = users.create_superuser(username="staff", password="x")
        self.pending = PDPBetaUser.objects.create(
            person=users.create_user(username="pending"), status=Status.REQUESTED
        )
        users.create_user(username="newcomer")
        self.client = APIClient()
        self.client.force_login(self.staff)

    def queued_for(self, action):
        with patch(QUEUE) as queue, self.captureOnCommitCallbacks(execute=True):
            action()
        return [call.args[0] for call in queue.call_args_list]

    def test_approving_from_the_dashboard_queues_one_email(self):
        url = reverse("beta-request-detail", kwargs={"pk": self.pending.pk})
        queued = self.queued_for(lambda: self.client.patch(url, {"status": "APPROVED"}))
        self.assertEqual(queued, [self.pending.pk])

    def test_granting_by_pennkey_queues_one_email(self):
        queued = self.queued_for(
            lambda: self.client.post(reverse("beta-request-list"), {"username": "newcomer"})
        )
        self.assertEqual(queued, [PDPBetaUser.objects.get(person__username="newcomer").pk])

    def test_the_admin_action_queues_one_email_each(self):
        model_admin = PDPBetaUserAdmin(PDPBetaUser, AdminSite())
        request = RequestFactory().get("/")
        request.user = self.staff
        request.session = {}
        request._messages = FallbackStorage(request)
        queued = self.queued_for(
            lambda: model_admin.approve(request, PDPBetaUser.objects.filter(pk=self.pending.pk))
        )
        self.assertEqual(queued, [self.pending.pk])

    def test_adding_someone_in_the_admin_emails_them(self):
        newcomer = get_user_model().objects.get(username="newcomer")
        queued = self.queued_for(
            lambda: self.client.post(
                reverse("admin:degree_pdpbetauser_add"),
                {"person": newcomer.pk, "status": "APPROVED"},
            )
        )
        self.assertEqual(queued, [PDPBetaUser.objects.get(person=newcomer).pk])

    def test_denying_sends_nothing(self):
        url = reverse("beta-request-detail", kwargs={"pk": self.pending.pk})
        self.assertEqual(self.queued_for(lambda: self.client.patch(url, {"status": "DENIED"})), [])

    def test_someone_already_emailed_is_not_emailed_again(self):
        self.pending.notified_at = timezone.now()
        self.pending.save()
        url = reverse("beta-request-detail", kwargs={"pk": self.pending.pk})
        self.assertEqual(
            self.queued_for(lambda: self.client.patch(url, {"status": "APPROVED"})), []
        )


@override_settings(SMTP_HOST="smtp.example.com")
class ApprovalEmailTaskTest(TestCase):
    def setUp(self):
        person = get_user_model().objects.create_user(
            username="quaker", first_name="Ben", email="ben@upenn.edu"
        )
        self.beta = PDPBetaUser.objects.create(person=person, status=Status.APPROVED)

    def test_sends_from_penn_course_alert_and_records_it(self):
        with patch("degree.tasks.send_email") as send:
            result = send_beta_approval_email(self.beta.pk)

        self.assertEqual(result["result"], "sent")
        kwargs = send.call_args.kwargs
        self.assertEqual(kwargs["to"], "ben@upenn.edu")
        self.assertIn("Penn Course Alert", kwargs["from_"])
        self.assertIn("Hi Ben", kwargs["html"])
        self.beta.refresh_from_db()
        self.assertIsNotNone(self.beta.notified_at)

    def test_never_sends_twice(self):
        with patch("degree.tasks.send_email") as send:
            send_beta_approval_email(self.beta.pk)
            send_beta_approval_email(self.beta.pk)
        self.assertEqual(send.call_count, 1)

    def test_falls_back_to_the_pennkey_address(self):
        self.beta.person.email = ""
        self.beta.person.save()
        with patch("degree.tasks.send_email") as send:
            send_beta_approval_email(self.beta.pk)
        self.assertEqual(send.call_args.kwargs["to"], "quaker@upenn.edu")

    @override_settings(SMTP_HOST="")
    def test_does_nothing_without_smtp(self):
        with patch("degree.tasks.send_email") as send:
            result = send_beta_approval_email(self.beta.pk)
        self.assertEqual(result["result"], "not configured")
        send.assert_not_called()
        self.beta.refresh_from_db()
        self.assertIsNone(self.beta.notified_at)

    def test_a_refused_address_is_not_marked_sent(self):
        refused = SMTPRecipientsRefused({"ben@upenn.edu": (550, b"no")})
        with patch("degree.tasks.send_email", side_effect=refused):
            result = send_beta_approval_email(self.beta.pk)
        self.assertEqual(result["result"], "refused")
        self.beta.refresh_from_db()
        self.assertIsNone(self.beta.notified_at)
