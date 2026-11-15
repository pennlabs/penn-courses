from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from degree.admin import PDPBetaUserAdmin
from degree.models import PDPBetaUser


Status = PDPBetaUser.Status


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
