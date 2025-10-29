from __future__ import annotations

from typing import Iterable, Sequence

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet

from ..models import ContactAttachment, ContactMessage


def add_message(
    *,
    first_name: str,
    last_name: str,
    phone: str,
    email: str,
    company: str,
    message: str,
    attachments: Sequence | None = None,
) -> tuple[ContactMessage, str]:
    files: list[UploadedFile] = list(attachments or [])
    with transaction.atomic():
        contact_message = ContactMessage.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            company=company,
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
        queryset = queryset.filter(company=company)

    order_by = _resolve_ordering(sort_by)
    if order_by:
        queryset = queryset.order_by(*order_by)

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
    if sort_by == "oldest":
        return ["created_at"]
    if sort_by == "status":
        return ["status", "-created_at"]
    if sort_by == "company":
        return ["company", "-created_at"]
    return ["-created_at"]


def _create_attachments(message: ContactMessage, files: Sequence[UploadedFile]) -> None:
    for uploaded in files:
        ContactAttachment.objects.create(
            message=message,
            file=uploaded,
            original_name=getattr(uploaded, "name", ""),
            content_type=getattr(uploaded, "content_type", ""),
            size=getattr(uploaded, "size", 0) or 0,
        )
