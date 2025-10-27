from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from contact.models import Activity, Department, Request, StaffProfile

User = get_user_model()


class RequestAccessTests(TestCase):
    def setUp(self) -> None:
        self.department = Department.objects.create(name="Cert", slug="cert")
        self.request = Request.objects.create(
            first_name="Jane",
            last_name="Doe",
            phone="123456",
            email="jane@example.com",
            company="ACME",
            message="Need help",
            department=self.department,
        )

    def test_valid_token_allows_access(self) -> None:
        url = reverse("contact:public-request", args=[self.request.pk])
        response = self.client.get(url)
        self.assertContains(response, "Access request", status_code=200)

        response = self.client.get(url + f"?access={self.request.access_token}")
        self.assertEqual(response.status_code, 302)
        follow = self.client.get(response["Location"])
        self.assertContains(follow, "Request #", status_code=200)
        self.assertNotIn(self.request.access_token, follow.content.decode())

    def test_invalid_or_disabled_token(self) -> None:
        url = reverse("contact:public-request", args=[self.request.pk])
        response = self.client.get(url + "?access=wrong")
        self.assertContains(response, "Access request", status_code=200)

        self.request.access_enabled = False
        self.request.save(update_fields=["access_enabled"])
        response = self.client.get(url + f"?access={self.request.access_token}")
        self.assertEqual(response.status_code, 403)

    def test_token_rotation_invalidates_old_link(self) -> None:
        old_token = self.request.access_token
        new_token = self.request.issue_access_token()
        url = reverse("contact:public-request", args=[self.request.pk])
        response = self.client.get(url + f"?access={old_token}")
        self.assertContains(response, "Access request", status_code=200)
        response = self.client.get(url + f"?access={new_token}")
        self.assertEqual(response.status_code, 302)


class AttachmentUploadTests(TestCase):
    def test_multiple_attachments_saved(self) -> None:
        url = reverse("contact:index")
        data = {
            "first_name": "John",
            "last_name": "Smith",
            "phone": "111",
            "email": "john@example.com",
            "company": "firma1",
            "message": "hello",
            "bot_check": "on",
        }
        file1 = SimpleUploadedFile("file1.pdf", b"PDF", content_type="application/pdf")
        file2 = SimpleUploadedFile("file2.png", b"PNG", content_type="image/png")
        payload = data | {"attachments": [file1, file2]}
        response = self.client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)
        request_obj = Request.objects.latest("pk")
        self.assertEqual(request_obj.attachments.count(), 2)

    def test_rejects_wrong_filetype(self) -> None:
        url = reverse("contact:index")
        data = {
            "first_name": "John",
            "last_name": "Smith",
            "phone": "111",
            "email": "john@example.com",
            "company": "firma1",
            "message": "hello",
            "bot_check": "on",
        }
        bad_file = SimpleUploadedFile("file.exe", b"bad", content_type="application/octet-stream")
        payload = data | {"attachments": [bad_file]}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertIn("Files of type application/octet-stream are not allowed.", form.errors["attachments"])


class StaffScopingTests(TestCase):
    def setUp(self) -> None:
        self.dept_a = Department.objects.create(name="Dept A", slug="dept-a")
        self.dept_b = Department.objects.create(name="Dept B", slug="dept-b")
        self.req_a = Request.objects.create(
            first_name="Ann",
            last_name="Lee",
            phone="1",
            email="ann@example.com",
            company="firma1",
            message="A",
            department=self.dept_a,
        )
        self.req_b = Request.objects.create(
            first_name="Bob",
            last_name="Roe",
            phone="2",
            email="bob@example.com",
            company="firma1",
            message="B",
            department=self.dept_b,
        )
        self.admin = User.objects.create_user("admin", password="pass")
        StaffProfile.objects.create(user=self.admin, role=StaffProfile.Role.ADMIN)
        self.employee = User.objects.create_user("employee", password="pass")
        StaffProfile.objects.create(user=self.employee, role=StaffProfile.Role.EMPLOYEE, department=self.dept_a)

    def test_employee_sees_only_own_department(self) -> None:
        client = Client()
        client.force_login(self.employee)
        response = client.get(reverse("contact:staff-request-list"))
        self.assertEqual(list(response.context["requests"]), [self.req_a])
        detail = client.get(reverse("contact:staff-request-detail", args=[self.req_b.pk]))
        self.assertEqual(detail.status_code, 403)

    def test_admin_has_full_access_and_filter(self) -> None:
        client = Client()
        client.force_login(self.admin)
        response = client.get(reverse("contact:staff-request-list"))
        self.assertCountEqual(response.context["requests"], [self.req_a, self.req_b])
        filtered = client.get(reverse("contact:staff-request-list"), {"department": self.dept_a.pk})
        self.assertEqual(list(filtered.context["requests"]), [self.req_a])
        detail = client.get(reverse("contact:staff-request-detail", args=[self.req_b.pk]))
        self.assertEqual(detail.status_code, 200)


class ActivityFeedTests(TestCase):
    def test_staff_actions_not_public(self) -> None:
        req = Request.objects.create(
            first_name="Kate",
            last_name="Doe",
            phone="123",
            email="kate@example.com",
            company="firma1",
            message="Hi",
        )
        Activity.objects.create(
            request=req,
            type=Activity.Type.STATUS_CHANGE,
            message="Status changed internally",
            is_public=False,
        )
        response = self.client.get(reverse("contact:index"))
        self.assertNotContains(response, "Status changed internally")
