from collections.abc import Iterable

from django.db.models import QuerySet

from ..models import ContactMessage


def add_message(*, first_name: str, last_name: str, phone: str, email: str, company: str, message: str) -> ContactMessage:
    return ContactMessage.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        company=company,
        message=message,
    )


def mark_messages_new(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids, is_deleted=False).update(
        status=ContactMessage.STATUS_NEW
    )


def mark_messages_in_progress(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids, is_deleted=False).update(
        status=ContactMessage.STATUS_IN_PROGRESS
    )


def mark_messages_ready(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids, is_deleted=False).update(
        status=ContactMessage.STATUS_READY
    )


def delete_messages(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).update(is_deleted=True)


def get_messages() -> QuerySet[ContactMessage]:
    return ContactMessage.objects.filter(is_deleted=False)


def get_deleted_messages() -> QuerySet[ContactMessage]:
    return ContactMessage.objects.filter(is_deleted=True)


def restore_messages(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).update(is_deleted=False)


def purge_messages(message_ids: Iterable[int] | None = None) -> None:
    queryset = ContactMessage.objects.filter(is_deleted=True)
    if message_ids is not None:
        queryset = queryset.filter(id__in=message_ids)
    queryset.delete()
