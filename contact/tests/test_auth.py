from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from contact.models import AdminUser


class LoginViewTests(TestCase):
    def test_admin_user_login_sets_session(self) -> None:
        AdminUser.objects.create(
            email='boss@example.com',
            token_hash=make_password('secret-token'),
            level=AdminUser.LEVEL_2,
            department='firma1',
        )
        response = self.client.post(
            reverse('contact:login'),
            {'email': 'boss@example.com', 'password': 'secret-token'},
        )
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertTrue(session.get('logged_in'))
        self.assertEqual(session.get('user_level'), AdminUser.LEVEL_2)
        self.assertEqual(session.get('user_department'), 'firma1')

    def test_invalid_token_returns_form_error(self) -> None:
        AdminUser.objects.create(
            email='boss@example.com',
            token_hash=make_password('secret-token'),
            level=AdminUser.LEVEL_1,
        )
        response = self.client.post(
            reverse('contact:login'),
            {'email': 'boss@example.com', 'password': 'wrong'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nieprawidłowy')
