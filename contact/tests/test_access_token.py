from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contact.models import ContactMessage


class AccessTokenTests(TestCase):
    def setUp(self) -> None:
        self.message = ContactMessage.objects.create(
            first_name='Alice',
            last_name='Smith',
            phone='+48111111111',
            email='alice@example.com',
            company='firma1',
            message='Question about services',
        )
        token = self.message.initialise_access_token()
        self.message.save(update_fields=['access_token_hash', 'access_token_expires_at'])
        self.token = token

    def test_token_expires_and_is_invalid(self) -> None:
        self.message.access_token_expires_at = timezone.now() - timedelta(minutes=5)
        self.message.save(update_fields=['access_token_expires_at'])

        self.assertTrue(self.message.is_access_token_expired)
        self.assertFalse(self.message.verify_access_token(self.token))

    def test_access_portal_rejects_expired_token(self) -> None:
        self.message.access_token_expires_at = timezone.now() - timedelta(minutes=5)
        self.message.save(update_fields=['access_token_expires_at'])

        response = self.client.post(
            reverse('contact:panel'),
            {
                'request_id': str(self.message.id),
                'access_token': self.token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Token wygasł', status_code=200)
