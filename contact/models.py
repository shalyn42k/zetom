from __future__ import annotations

import hashlib
import math
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import validate_slug
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True, validators=[validate_slug])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.name


class StaffProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Administrator")
        EMPLOYEE = "employee", _("Employee")

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=16, choices=Role.choices)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="staff_members",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("staff profile")
        verbose_name_plural = _("staff profiles")

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.user} ({self.get_role_display()})"


class Request(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "ready"

    STATUS_CHOICES = [
        (STATUS_NEW, "new"),
        (STATUS_IN_PROGRESS, "in_progress"),
        (STATUS_READY, "ready"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50)
    message = models.TextField()
    final_changes = models.TextField(blank=True)
    final_response = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="requests",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="requests_created",
        null=True,
        blank=True,
    )

    access_token = models.CharField(max_length=64, editable=False, unique=True)
    access_token_hash = models.CharField(max_length=128, editable=False, blank=True)
    access_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "contact_contactmessage"

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.first_name} {self.last_name} ({self.email})"

    # Token -----------------------------------------------------------------
    @staticmethod
    def _token_length() -> int:
        length = getattr(settings, "REQUEST_TOKEN_LENGTH", 40)
        return max(32, min(48, int(length)))

    @classmethod
    def _generate_token(cls) -> str:
        target_length = cls._token_length()
        # token_urlsafe produces 1.3 * nbytes characters; derive nbytes accordingly.
        nbytes = max(24, math.ceil(target_length * 3 / 4))
        token = secrets.token_urlsafe(nbytes)
        if len(token) > target_length:
            token = token[:target_length]
        while len(token) < target_length:
            token += secrets.token_urlsafe(4)
            if len(token) > target_length:
                token = token[:target_length]
        return token

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def issue_access_token(self, *, commit: bool = True) -> str:
        """Rotate the access token and return the plain value."""

        with transaction.atomic():
            for _ in range(10):
                token = self._generate_token()
                if not Request.objects.exclude(pk=self.pk).filter(access_token=token).exists():
                    break
            else:  # pragma: no cover - highly unlikely
                raise RuntimeError("Unable to generate a unique access token")

            self.access_token = token
            self.access_token_hash = self._hash_token(token)
            if commit:
                self.save(update_fields=["access_token", "access_token_hash"])
        return token

    def verify_access_token(self, raw_token: str | None) -> bool:
        if not raw_token or not self.access_enabled:
            return False
        if self.access_token_hash:
            return constant_time_compare(self.access_token_hash, self._hash_token(raw_token))
        return constant_time_compare(self.access_token, raw_token)

    def disable_access(self) -> None:
        if self.access_enabled:
            self.access_enabled = False
            self.save(update_fields=["access_enabled"])

    def enable_access(self) -> None:
        if not self.access_enabled:
            self.access_enabled = True
            self.save(update_fields=["access_enabled"])

    def save(self, *args, **kwargs):
        if not self.access_token:
            # Generate once for freshly created records.
            self.issue_access_token(commit=False)
        super().save(*args, **kwargs)


def attachment_upload_to(instance: "Attachment", filename: str) -> str:
    from uuid import uuid4

    suffix = filename.split(".")[-1] if "." in filename else ""
    fragment = uuid4().hex
    request_id = instance.request_id or "pending"
    if suffix:
        return f"requests/{request_id}/{fragment}.{suffix}"
    return f"requests/{request_id}/{fragment}"


class Attachment(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_to)
    original_name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    content_type = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_attachments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return self.original_name


class Activity(models.Model):
    class Type(models.TextChoices):
        COMMENT = "comment", _("Comment")
        STATUS_CHANGE = "status_change", _("Status change")
        ASSIGNMENT = "assignment", _("Assignment")
        FILE_UPLOAD = "file_upload", _("File upload")
        SYSTEM = "system", _("System")

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="request_activities",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    message = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.get_type_display()} @ {self.created_at:%Y-%m-%d %H:%M}"

