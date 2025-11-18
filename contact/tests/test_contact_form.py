from __future__ import annotations

import json

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
            'full_name': 'John Doe',
            'phone': '+48123123123',
            'email': 'john@example.com',
            'company': 'firma1',
            'company_name': 'Acme Sp. z o.o.',
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

    def test_index_includes_active_request_context(self) -> None:
        message = ContactMessage.objects.create(
            full_name='Jane Doe',
            phone='+48123456789',
            email='jane@example.com',
            company='firma1',
            company_name='Example Sp. z o.o.',
            message='Need assistance',
        )
        session = self.client.session
        session['user_message_ids'] = [message.id]
        session.save()

        response = self.client.get(reverse('contact:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_request_id'], message.id)
        self.assertTrue(response.context['has_active_request'])
        payload = json.loads(response.context['active_request_json'])
        self.assertEqual(payload['id'], message.id)
        self.assertEqual(payload['full_name'], 'Jane Doe')

    def test_index_skips_deleted_or_expired_requests(self) -> None:
        message = ContactMessage.objects.create(
            full_name='Old Entry',
            phone='+48111222333',
            email='old@example.com',
            company='firma1',
            company_name='Old Co',
            message='Archived',
            is_deleted=True,
        )
        session = self.client.session
        session['user_message_ids'] = [message.id]
        session.save()

        response = self.client.get(reverse('contact:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['active_request_id'])
        self.assertFalse(response.context['has_active_request'])
