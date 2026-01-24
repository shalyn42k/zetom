"""
# === FILE SUMMARY ===
# Purpose: Defines database models for contact messages, attachments, departments, admin users, activity logs, and change tracking.
# Responsible for: Persisting contact-related data, access tokens, admin credentials, and audit trails.
# Connected to: Django settings for token TTL, contact services and views, authentication helpers.
# Important classes/functions: ContactMessage, ContactAttachment, Department, AdminUser, AdminActivityLog, ClientChangeLog, _generate_access_token()
# Notes: Models include helper methods for token creation and password hashing to support portal workflows.
# =====================================
"""

from __future__ import annotations

import secrets

from datetime import timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.db import models
from django.utils import timezone

from .departments import DEFAULT_DEPARTMENTS



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
    assigned_to = models.ForeignKey(
        "AdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_messages",
    )

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


class Department(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name_pl = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - representation helper
        return f"Department({self.code})"
def ensure_default_departments() -> None:
    existing_codes = set(Department.objects.values_list("code", flat=True))
    missing = [
        Department(code=code, name_pl=name_pl, name_en=name_en)
        for code, name_pl, name_en in DEFAULT_DEPARTMENTS
        if code not in existing_codes
    ]
    if missing:
        Department.objects.bulk_create(missing, ignore_conflicts=True)


class AdminUser(models.Model):
    LEVEL_ADMIN = "level1"
    LEVEL_DEPARTMENT = "level2"
    LEVEL_TESTER = "level3"

    LEVEL_CHOICES = [
        (LEVEL_ADMIN, "level1"),
        (LEVEL_DEPARTMENT, "level2"),
        (LEVEL_TESTER, "level3"),
    ]

    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    level_of_access = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    departments = models.ManyToManyField(Department, related_name="admins", blank=True)
    permissions_override = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_password_reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - representation helper
        return f"AdminUser({self.email}, {self.level_of_access})"

    def set_password(self, raw: str) -> None:
        self.password_hash = make_password(raw)

    def check_password(self, raw: str) -> bool:
        return check_password(raw, self.password_hash)

    def permission_profile(self) -> dict[str, object]:
        return resolve_permission_profile(self.level_of_access, self.permissions_override)

    def permissions(self) -> dict[str, bool]:
        profile = self.permission_profile()
        permissions = profile.get("permissions", {})
        return {key: bool(permissions.get(key)) for key in PERMISSION_KEYS}

    def has_permission(self, key: str) -> bool:
        return bool(self.permissions().get(key))

    @property
    def can_edit_messages(self) -> bool:
        return self.has_permission("can_edit_messages")

    @property
    def can_delete_messages(self) -> bool:
        return self.has_permission("can_delete_messages")

    @property
    def can_export_messages(self) -> bool:
        return self.has_permission("can_export_messages")

    @property
    def can_send_emails(self) -> bool:
        return self.has_permission("can_send_emails")

    @property
    def can_view_all_messages(self) -> bool:
        return self.has_permission("can_view_all_messages")

    def save(self, *args, **kwargs) -> None:
        if self.password_hash:
            try:
                identify_hasher(self.password_hash)
            except ValueError:
                self.password_hash = make_password(self.password_hash)
        super().save(*args, **kwargs)


PERMISSION_KEYS: tuple[str, ...] = (
    "can_edit_messages",
    "can_delete_messages",
    "can_export_messages",
    "can_send_emails",
    "can_view_all_messages",
)


ROLE_PERMISSION_PROFILES: dict[str, dict[str, bool]] = {
    AdminUser.LEVEL_ADMIN: {
        "can_edit_messages": True,
        "can_delete_messages": True,
        "can_export_messages": True,
        "can_send_emails": True,
        "can_view_all_messages": True,
    },
    AdminUser.LEVEL_DEPARTMENT: {
        "can_edit_messages": True,
        "can_delete_messages": True,
        "can_export_messages": True,
        "can_send_emails": True,
        "can_view_all_messages": True,
    },
    AdminUser.LEVEL_TESTER: {
        "can_edit_messages": False,
        "can_delete_messages": False,
        "can_export_messages": False,
        "can_send_emails": False,
        "can_view_all_messages": False,
    },
}


def default_permissions_for_level(level: str) -> dict[str, bool]:
    return ROLE_PERMISSION_PROFILES.get(level, ROLE_PERMISSION_PROFILES[AdminUser.LEVEL_TESTER]).copy()


def resolve_permission_profile(level: str, override: dict | None) -> dict[str, object]:
    base = default_permissions_for_level(level)
    raw_override = override or {}
    mode = raw_override.get("mode") if isinstance(raw_override, dict) else None
    selected_mode = "custom" if mode == "custom" else "inherit"
    if selected_mode == "custom":
        custom_values = raw_override.get("permissions") if isinstance(raw_override, dict) else None
        if isinstance(custom_values, dict):
            for key in PERMISSION_KEYS:
                if key in custom_values:
                    base[key] = bool(custom_values[key])
    return {"mode": selected_mode, "permissions": base}


def build_permissions_override(level: str, override: dict | None) -> dict[str, object]:
    profile = resolve_permission_profile(level, override)
    if profile["mode"] != "custom":
        return {"mode": "inherit", "permissions": {}}
    permissions = profile.get("permissions") or {}
    return {
        "mode": "custom",
        "permissions": {key: bool(permissions.get(key, False)) for key in PERMISSION_KEYS},
    }

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
