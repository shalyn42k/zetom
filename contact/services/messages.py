from collections.abc import Iterable

from django.db.models import QuerySet

from ..models import Request


def add_message(*, first_name: str, last_name: str, phone: str, email: str, company: str, message: str) -> Request:
    return Request.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        company=company,
        message=message,
    )


def update_messages_status(message_ids: Iterable[int], *, status: str) -> None:
    Request.objects.filter(id__in=message_ids, is_deleted=False).update(
        status=status
    )


def delete_messages(message_ids: Iterable[int]) -> None:
    Request.objects.filter(id__in=message_ids).update(is_deleted=True)


def get_messages(*, sort_by: str | None = None, company: str | None = None) -> QuerySet[Request]:
    queryset = Request.objects.filter(is_deleted=False)

    if company and company != "all":
        queryset = queryset.filter(company=company)

    order_by = _resolve_ordering(sort_by)
    if order_by:
        queryset = queryset.order_by(*order_by)

    return queryset


def get_deleted_messages() -> QuerySet[Request]:
    return Request.objects.filter(is_deleted=True)


def restore_messages(message_ids: Iterable[int]) -> None:
    Request.objects.filter(id__in=message_ids).update(is_deleted=False)


def purge_messages(message_ids: Iterable[int] | None = None) -> None:
    queryset = Request.objects.filter(is_deleted=True)
    if message_ids is not None:
        queryset = queryset.filter(id__in=message_ids)
    queryset.delete()


def _resolve_ordering(sort_by: str | None) -> list[str]:
    if sort_by == "oldest":
        return ["created_at"]
    if sort_by == "status":
        return ["status", "-created_at"]
    if sort_by == "company":
        return ["company", "-created_at"]
    return ["-created_at"]
