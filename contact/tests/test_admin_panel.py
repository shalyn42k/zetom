from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse

from contact.forms import MessageBulkActionForm, TrashActionForm
from contact.models import ContactMessage


@override_settings(COMPANY_NOTIFICATION_RECIPIENTS={'default': []}, SMTP_USER='')
class AdminPanelTests(TestCase):
    def setUp(self) -> None:
        self.message = ContactMessage.objects.create(
            full_name='Jane Doe',
            phone='+48123123123',
            email='jane@example.com',
            company='firma1',
            company_name='JD Consulting',
            message='Need help',
        )
        session = self.client.session
        session['logged_in'] = True
        session.save()

    def test_bulk_action_updates_status(self) -> None:
        url = reverse('contact:panel')
        response = self.client.post(
            url,
            {
                'form_name': 'bulk',
                'action': MessageBulkActionForm.ACTION_MARK_READY,
                'selected': [str(self.message.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.STATUS_READY)

    def test_trash_restore_flow(self) -> None:
        url = reverse('contact:panel')
        delete_response = self.client.post(
            url,
            {
                'form_name': 'bulk',
                'action': MessageBulkActionForm.ACTION_DELETE,
                'selected': [str(self.message.id)],
            },
        )
        self.assertEqual(delete_response.status_code, 302)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_deleted)

        # Reload panel to populate trash choices with the deleted message
        self.client.get(url)

        restore_response = self.client.post(
            url,
            {
                'form_name': 'trash',
                'action': TrashActionForm.ACTION_RESTORE,
                'selected': [str(self.message.id)],
            },
        )
        self.assertEqual(restore_response.status_code, 302)
        self.message.refresh_from_db()
        self.assertFalse(self.message.is_deleted)
