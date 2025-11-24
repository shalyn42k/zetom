from __future__ import annotations

from typing import Iterable, Sequence

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet

from ..models import ContactAttachment, ContactMessage


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
    files: list[UploadedFile] = list(attachments or [])
    with transaction.atomic():
        contact_message = ContactMessage.objects.create(
            full_name=full_name,
            phone=phone,
            email=email,
            company=company,
            company_name=company_name,
            message=message,
        )
        token = contact_message.initialise_access_token()
        contact_message.save(update_fields=["access_token_hash", "access_token_expires_at"])
if files:
    _create_attachments(contact_message, files, language='pl') 
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


def add_attachments(message: ContactMessage, files: Sequence[UploadedFile], language: str = 'pl') -> None:
    if not files:
        return
    _create_attachments(message, files, language=language)


def _resolve_ordering(sort_by: str | None) -> list[str]:
    if sort_by == "oldest":
        return ["created_at"]
    if sort_by == "status":
        return ["status", "-created_at"]
    if sort_by == "company":
        return ["company", "-created_at"]
    return ["-created_at"]

def _create_attachments(message: ContactMessage, files: Sequence[UploadedFile], language: str = 'pl') -> None:
    from contact.services.file_scanner import validate_and_scan_uploaded_file
    import os

    for uploaded in files:
        if uploaded.size == 0:
            continue

        # Сначала сохраняем файл временно
        attachment = ContactAttachment(
            message=message,
            original_name=uploaded.name,
            content_type=uploaded.content_type or '',
            size=uploaded.size,
        )
        attachment.file.save(uploaded.name, uploaded, save=False)
        full_path = attachment.file.path

        try:
            # ПРОВЕРКА НА ВИРУСЫ И ТИП
            validate_and_scan_uploaded_file(full_path, language=language)

            # Если всё ок — сохраняем в БД
            attachment.save()

        except Exception as e:
            # Если вирус или ошибка — удаляем файл с диска
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except:
                    pass
            raise  # пробрасываем ошибку дальше (в форму)