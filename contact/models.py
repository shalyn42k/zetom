from __future__ import annotations

import secrets

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


def _generate_access_token() -> str:
    """Return a URL-safe access token between 32 and 48 characters."""

    # secrets.token_urlsafe(n) ≈ ceil(n * 4 / 3) chars; 24 → 32, 32 → 43.
    # Generate until the length constraints are satisfied.
    for size in (32, 40, 48):
        token = secrets.token_urlsafe(size)
        if 32 <= len(token) <= 48:
            return token
    # Fallback in the unlikely event none of the above matched the range.
    return secrets.token_urlsafe(36)


class ContactMessage(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "ready"

    STATUS_CHOICES = [
        (STATUS_NEW, "new"),
        (STATUS_IN_PROGRESS, "in_progress"),
        (STATUS_READY, "ready"),
    ]

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50, db_index=True)
    company_name = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    final_changes = models.TextField(blank=True)
    final_response = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    access_token_hash = models.CharField(max_length=128, blank=True)
    access_enabled = models.BooleanField(default=True)
    access_token_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"

    def initialise_access_token(self) -> str:
        """Create and store a hashed access token, returning the raw token."""

        token = _generate_access_token()
        self.access_token_hash = make_password(token)
        ttl_hours = max(1, getattr(settings, 'CONTACT_ACCESS_TOKEN_TTL_HOURS', 72))
        self.access_token_expires_at = timezone.now() + timedelta(hours=ttl_hours)
        return token

    def verify_access_token(self, token: str) -> bool:
        if not token or not self.access_token_hash:
            return False
        if self.is_access_token_expired:
            return False
        return check_password(token, self.access_token_hash)

    @property
    def is_access_token_expired(self) -> bool:
        expires_at = self.access_token_expires_at
        if not expires_at:
            return False
        return timezone.now() > expires_at


class ContactAttachment(models.Model):
    message = models.ForeignKey(
        ContactMessage,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to="attachments/%Y/%m/%d")
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:  # pragma: no cover - representation helper
        return f"Attachment({self.original_name})"


class AdminActivityLog(models.Model):
    ACTION_STATUS_CHANGE = "status_change"
    ACTION_DELETE = "delete"
    ACTION_RESTORE = "restore"
    ACTION_PURGE = "purge"
    ACTION_EMAIL = "email"
    ACTION_ROLLBACK = "rollback"

    ACTION_CHOICES = [
        (ACTION_STATUS_CHANGE, "status_change"),
        (ACTION_DELETE, "delete"),
        (ACTION_RESTORE, "restore"),
        (ACTION_PURGE, "purge"),
        (ACTION_EMAIL, "email"),
        (ACTION_ROLLBACK, "rollback"),
    ]

    message = models.ForeignKey(
        ContactMessage,
        related_name="admin_logs",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class ClientChangeLog(models.Model):
    FIELD_FULL_NAME = "full_name"
    FIELD_PHONE = "phone"
    FIELD_EMAIL = "email"
    FIELD_COMPANY = "company"
    FIELD_COMPANY_NAME = "company_name"
    FIELD_MESSAGE = "message"

    FIELD_CHOICES = [
        (FIELD_FULL_NAME, "full_name"),
        (FIELD_PHONE, "phone"),
        (FIELD_EMAIL, "email"),
        (FIELD_COMPANY, "company"),
        (FIELD_COMPANY_NAME, "company_name"),
        (FIELD_MESSAGE, "message"),
    ]

    message = models.ForeignKey(
        ContactMessage,
        related_name="client_logs",
        on_delete=models.CASCADE,
    )
    field = models.CharField(max_length=32, choices=FIELD_CHOICES)
    previous_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_reverted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-changed_at", "-id"]
