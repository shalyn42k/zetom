from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse

from contact.forms import MessageBulkActionForm, MessageFilterForm, TrashActionForm
from contact.models import AdminUser, ContactMessage, Department


@override_settings(COMPANY_NOTIFICATION_RECIPIENTS={'default': []}, SMTP_USER='')
class AdminPanelTests(TestCase):
    def setUp(self) -> None:
        self.department, _ = Department.objects.get_or_create(
            code='firma1',
            defaults={'name_pl': 'Firma 1', 'name_en': 'Company 1'},
        )
        self.message = ContactMessage.objects.create(
            full_name='Jane Doe',
            phone='+48123123123',
            email='jane@example.com',
            company='firma1',
            company_name='JD Consulting',
            message='Need help',
        )
        self.admin_user = AdminUser.objects.create(
            email='admin@example.com',
            password_hash='',
            level_of_access=AdminUser.LEVEL_ADMIN,
        )
        self.admin_user.set_password('password123')
        self.admin_user.save()
        self.admin_user.departments.add(self.department)
        session = self.client.session
        session['logged_in'] = True
        session['admin_user_id'] = self.admin_user.id
        session['level_of_access'] = self.admin_user.level_of_access
        session['departments'] = [self.department.code]
        session['admin_email'] = self.admin_user.email
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


@override_settings(COMPANY_NOTIFICATION_RECIPIENTS={'default': []}, SMTP_USER='')
class Level2AdminPanelTests(TestCase):
    def setUp(self) -> None:
        self.department1, _ = Department.objects.get_or_create(
            code='firma1',
            defaults={'name_pl': 'Firma 1', 'name_en': 'Company 1'},
        )
        self.department2, _ = Department.objects.get_or_create(
            code='firma2',
            defaults={'name_pl': 'Firma 2', 'name_en': 'Company 2'},
        )
        self.department_other, _ = Department.objects.get_or_create(
            code='inna',
            defaults={'name_pl': 'Inna', 'name_en': 'Other'},
        )

        self.message_dept1 = ContactMessage.objects.create(
            full_name='Jane Doe',
            phone='+48123123123',
            email='jane@example.com',
            company=self.department1.code,
            company_name='JD Consulting',
            message='Need help',
        )
        self.message_dept2 = ContactMessage.objects.create(
            full_name='John Smith',
            phone='+48123123123',
            email='john@example.com',
            company=self.department2.code,
            company_name='JS Consulting',
            message='Need help too',
        )
        self.message_other = ContactMessage.objects.create(
            full_name='Mark Agent',
            phone='+48123123123',
            email='mark@example.com',
            company=self.department_other.code,
            company_name='Other Ltd',
            message='Hidden request',
        )

        self.level2_user = AdminUser.objects.create(
            email='dept@example.com',
            password_hash='',
            level_of_access=AdminUser.LEVEL_DEPARTMENT,
        )
        self.level2_user.set_password('password123')
        self.level2_user.save()
        self.level2_user.departments.add(self.department1, self.department2)

        session = self.client.session
        session['logged_in'] = True
        session['admin_user_id'] = self.level2_user.id
        session['level_of_access'] = self.level2_user.level_of_access
        session['departments'] = list(
            self.level2_user.departments.values_list('code', flat=True)
        )
        session['admin_email'] = self.level2_user.email
        session.save()

    def test_level2_filtering_respects_assigned_departments(self) -> None:
        url = reverse('contact:panel')
        response = self.client.get(url, {'company': 'inna'})

        self.assertEqual(response.status_code, 200)
        companies = {
            message.company for message in response.context['messages_page'].object_list
        }
        self.assertEqual(companies, {self.department1.code, self.department2.code})

        company_choices = [value for value, _ in response.context['filter_form'].fields['company'].choices]
        self.assertIn(MessageFilterForm.COMPANY_ALL, company_choices)
        self.assertIn(self.department1.code, company_choices)
        self.assertIn(self.department2.code, company_choices)
        self.assertNotIn(self.department_other.code, company_choices)

    def test_level2_bulk_actions_skip_unassigned_departments(self) -> None:
        url = reverse('contact:panel')
        response = self.client.post(
            url,
            {
                'form_name': 'bulk',
                'action': MessageBulkActionForm.ACTION_MARK_READY,
                'selected': [
                    str(self.message_dept1.id),
                    str(self.message_other.id),
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.message_dept1.refresh_from_db()
        self.message_other.refresh_from_db()

        self.assertEqual(self.message_dept1.status, ContactMessage.STATUS_READY)
        self.assertEqual(self.message_other.status, ContactMessage.STATUS_NEW)
