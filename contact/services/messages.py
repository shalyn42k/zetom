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


def mark_messages_read(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).update(is_read=True)


def delete_messages(message_ids: Iterable[int]) -> None:
    ContactMessage.objects.filter(id__in=message_ids).delete()


def get_messages() -> QuerySet[ContactMessage]:
    return ContactMessage.objects.all()
