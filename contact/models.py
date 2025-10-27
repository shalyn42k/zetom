from __future__ import annotations

import secrets

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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50)
    message = models.TextField()
    final_changes = models.TextField(blank=True)
    final_response = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    access_token_hash = models.CharField(max_length=128, blank=True)
    access_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

    def initialise_access_token(self) -> str:
        """Create and store a hashed access token, returning the raw token."""

        token = _generate_access_token()
        self.access_token_hash = make_password(token)
        return token

    def verify_access_token(self, token: str) -> bool:
        if not token or not self.access_token_hash:
            return False
        return check_password(token, self.access_token_hash)


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
