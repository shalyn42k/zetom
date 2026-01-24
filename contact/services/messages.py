"""
# === FILE SUMMARY ===
# Purpose: Service layer for CRUD operations on contact messages and attachments.
# Responsible for: Creating messages with access tokens, updating status, soft-deleting/restoring, purging, and ordering results.
# Connected to: ContactMessage and ContactAttachment models, views that orchestrate user/admin flows.
# Important classes/functions: add_message(), update_messages_status(), delete_messages(), get_messages(), get_deleted_messages(), restore_messages(), purge_messages(), add_attachments()
# Notes: Uses database transactions to ensure message creation with attachments is atomic.
# =====================================
"""

from __future__ import annotations

from typing import Iterable, Sequence

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Case, IntegerField, QuerySet, When

from ..departments import normalize_department_code
from ..models import ContactAttachment, ContactMessage, Department


def add_message(
    *,
    full_name: str,
    phone: str,
    email: str,
    company: str,
    company_name: str,
    message: str,
    attachments: Sequence | None = None,
) -> tuple[ContactMessage, str]:
    company = normalize_department_code(company)
    files: list[UploadedFile] = list(attachments or [])
    department = Department.objects.filter(code=company).first()
    with transaction.atomic():
        contact_message = ContactMessage.objects.create(
            full_name=full_name,
            phone=phone,
            email=email,
            company=company,
            department=department,
            company_name=company_name,
            message=message,
        )
        token = contact_message.initialise_access_token()
        contact_message.save(update_fields=["access_token_hash", "access_token_expires_at"])
        if files:
            _create_attachments(contact_message, files)
    return contact_message, token


def update_messages_status(message_ids: Iterable[int], *, status: str) -> None:
    ContactMessage.objects.filter(id__in=message_ids, is_deleted=False).update(
        status=status
    )


def delete_messages(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).update(is_deleted=True)


def get_messages(*, sort_by: str | None = None, company: str | None = None) -> QuerySet[ContactMessage]:
    queryset = ContactMessage.objects.filter(is_deleted=False).prefetch_related('attachments')

    if company and company != "all":
        if isinstance(company, (list, tuple, set)):
            queryset = queryset.filter(company__in=company)
        else:
            queryset = queryset.filter(company=company)

    queryset = _apply_sorting(queryset, sort_by)

    return queryset


def get_deleted_messages() -> QuerySet[ContactMessage]:
    return ContactMessage.objects.filter(is_deleted=True).prefetch_related('attachments')


def restore_messages(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).update(is_deleted=False)


def purge_messages(message_ids: Iterable[int] | None = None) -> None:
    queryset = ContactMessage.objects.filter(is_deleted=True)
    if message_ids is not None:
        queryset = queryset.filter(id__in=message_ids)
    queryset.delete()


def add_attachments(message: ContactMessage, files: Sequence[UploadedFile]) -> None:
    if not files:
        return
    _create_attachments(message, files)


def _resolve_ordering(sort_by: str | None) -> list[str]:
    """Legacy helper kept for backwards compatibility."""
    # NOTE: Retained for imports elsewhere; admin panel now uses _apply_sorting
    # for explicit ordering rules. This function mirrors those rules.
    if sort_by == "oldest":
        return ["created_at", "id"]
    if sort_by == "status":
        return ["status", "-created_at", "-id"]
    if sort_by == "company":
        return ["company", "-created_at", "-id"]
    return ["-created_at", "-id"]


def _apply_sorting(queryset: QuerySet[ContactMessage], sort_by: str | None) -> QuerySet[ContactMessage]:
    """Apply explicit ORM ordering for admin panel sorting options."""

    if sort_by == "oldest":
        return queryset.order_by("created_at", "id")

    if sort_by == "status":
        status_order = Case(
            When(status=ContactMessage.STATUS_NEW, then=0),
            When(status=ContactMessage.STATUS_IN_PROGRESS, then=1),
            When(status=ContactMessage.STATUS_READY, then=2),
            default=99,
            output_field=IntegerField(),
        )
        return queryset.annotate(_status_order=status_order).order_by(
            "_status_order", "-created_at", "-id"
        )

    if sort_by == "company":
        return queryset.order_by("company", "-created_at", "-id")

    return queryset.order_by("-created_at", "-id")


def _create_attachments(message: ContactMessage, files: Sequence[UploadedFile]) -> None:
    for uploaded in files:
        ContactAttachment.objects.create(
            message=message,
            file=uploaded,
            original_name=getattr(uploaded, "name", ""),
            content_type=getattr(uploaded, "content_type", ""),
            size=getattr(uploaded, "size", 0) or 0,
        )
