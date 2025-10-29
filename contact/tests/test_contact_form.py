from __future__ import annotations

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from contact.models import ContactMessage


@override_settings(
    CONTACT_FORM_THROTTLE_SECONDS=60,
    COMPANY_NOTIFICATION_RECIPIENTS={'default': []},
    SMTP_USER='',
    ATTACH_SCAN_COMMAND='',
)
class ContactFormTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def _valid_payload(self) -> dict[str, str | bool]:
        return {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+48123123123',
            'email': 'john@example.com',
            'company': 'firma1',
            'message': 'Hello there!',
            'bot_check': True,
        }

    def test_contact_form_submission_triggers_rate_limit(self) -> None:
        url = reverse('contact:index')
        response = self.client.post(url, self._valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

        response = self.client.post(url, self._valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proszę poczekać', status_code=200)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_attachment_validation_rejects_empty_file(self) -> None:
        url = reverse('contact:index')
        payload = self._valid_payload()
        payload['attachments'] = [
            SimpleUploadedFile('empty.pdf', b'', content_type='application/pdf')
        ]

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'jest pusty', status_code=200)
        self.assertEqual(ContactMessage.objects.count(), 0)
