from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserRegistrationModel
import os


class AdminWorkflowAndSecurityTest(TestCase):
    """
    Tests administrator authentication, RBAC authorization boundaries, and user activation.
    """

    def setUp(self):
        self.client = Client()
        self.admin_login_url = reverse('AdminLoginCheck')
        self.admin_home_url = reverse('adminhome')
        self.user_audit_url = reverse('RegisterUsersView')
        self.activate_url = reverse('activate_users')
        self.delete_url = reverse('delete_users')
        self.logout_url = reverse('AdminLogout')

        self.user = UserRegistrationModel.objects.create(
            name="Applicant One",
            loginid="applicant1",
            password="pbkdf2_sha256$testpasswordhash",
            mobile="9000000001",
            email="app1@example.com",
            status="waiting"
        )

    def test_unauthenticated_admin_access_redirects(self):
        # Accessing admin dashboard without admin session must redirect to login
        response = self.client.get(self.admin_home_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('Adminlogin', response.url)

    def test_unauthenticated_user_activation_blocked(self):
        # Direct attempt to activate user without admin session must fail and redirect
        response = self.client.post(self.activate_url, {'uid': self.user.id})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, 'waiting')

    def test_admin_login_success(self):
        # Admin login with valid credentials
        response = self.client.post(self.admin_login_url, {
            'loginid': 'admin',
            'pswd': 'admin'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('is_admin'), True)

    def test_admin_activation_workflow(self):
        # Login admin first
        session = self.client.session
        session['is_admin'] = True
        session.save()

        # Activate user via POST
        response = self.client.post(self.activate_url, {'uid': self.user.id})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, 'activated')

    def test_admin_delete_workflow(self):
        # Login admin first
        session = self.client.session
        session['is_admin'] = True
        session.save()

        # Delete user via POST
        response = self.client.post(self.delete_url, {'uid': self.user.id})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserRegistrationModel.objects.filter(id=self.user.id).exists())

    def test_admin_logout(self):
        session = self.client.session
        session['is_admin'] = True
        session.save()

        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get('is_admin'))
