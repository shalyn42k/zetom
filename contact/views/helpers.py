from __future__ import annotations

from typing import Callable, Iterable, Sequence
from urllib.parse import urlencode

from django.contrib import messages
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from ..forms import (
    ContactForm,
    MessageBulkActionForm,
    MessageFilterForm,
    TrashActionForm,
)
from ..models import AdminActivityLog, ContactAttachment, ContactMessage
from ..services import messages as message_service
from ..services.activity_log import log_action, log_bulk_action


def remember_user_message(request: HttpRequest, message_id: int) -> None:
    stored_ids = get_user_message_ids(request)
    if message_id not in stored_ids:
        stored_ids.append(message_id)
    store_user_message_ids(request, stored_ids)


def store_user_message_ids(request: HttpRequest, message_ids: Sequence[int]) -> None:
    unique_ids = list(dict.fromkeys(int(mid) for mid in message_ids))
    request.session['user_message_ids'] = unique_ids


def get_user_message_ids(request: HttpRequest) -> list[int]:
    raw_ids = request.session.get('user_message_ids', [])
    result: list[int] = []
    for value in raw_ids:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def remove_user_message(request: HttpRequest, message_id: int) -> None:
    remaining = [mid for mid in get_user_message_ids(request) if mid != int(message_id)]
    store_user_message_ids(request, remaining)


def user_can_access_message(request: HttpRequest, message_id: int) -> bool:
    return int(message_id) in get_user_message_ids(request)


def panel_redirect_url(
    lang: str,
    page_number: int | str | None,
    *,
    sort_by: str | None = None,
    company: str | None = None,
) -> str:
    base_url = reverse('contact:panel')
    params: dict[str, str] = {}
    if lang:
        params['lang'] = str(lang)
    if page_number:
        params['page'] = str(page_number)
    if sort_by:
        params['sort_by'] = str(sort_by)
    if company:
        params['company'] = str(company)
    if not params:
        return base_url
    return f"{base_url}?{urlencode(params)}"


def company_options(language: str) -> list[dict[str, str]]:
    labels = company_labels(language)
    return [
        {
            'value': value,
            'label': labels.get(value, label),
        }
        for value, label in ContactForm.COMPANY_CHOICES
    ]


def company_labels(language: str) -> dict[str, str]:
    if language == 'pl':
        return {value: label for value, label in ContactForm.COMPANY_CHOICES}
    return {
        'firma1': 'Company 1',
        'firma2': 'Company 2',
        'firma3': 'Company 3',
        'inna': 'Other',
    }


def status_options(language: str) -> list[dict[str, str]]:
    if language == 'pl':
        labels = {
            ContactMessage.STATUS_NEW: 'Nowe',
            ContactMessage.STATUS_IN_PROGRESS: 'W trakcie',
            ContactMessage.STATUS_READY: 'Gotowe',
        }
    else:
        labels = {
            ContactMessage.STATUS_NEW: 'New',
            ContactMessage.STATUS_IN_PROGRESS: 'In progress',
            ContactMessage.STATUS_READY: 'Ready',
        }
    return [
        {
            'value': ContactMessage.STATUS_NEW,
            'label': labels[ContactMessage.STATUS_NEW],
            'badge': 'badge--success',
        },
        {
            'value': ContactMessage.STATUS_IN_PROGRESS,
            'label': labels[ContactMessage.STATUS_IN_PROGRESS],
            'badge': 'badge--warning',
        },
        {
            'value': ContactMessage.STATUS_READY,
            'label': labels[ContactMessage.STATUS_READY],
            'badge': 'badge--info',
        },
    ]


def resolve_filter_data(request: HttpRequest, language: str) -> dict[str, str]:
    data = request.GET if request.method == 'GET' else request.POST
    if not data or ('sort_by' not in data and 'company' not in data):
        return {
            'sort_by': MessageFilterForm.SORT_NEWEST,
            'company': MessageFilterForm.COMPANY_ALL,
        }

    filter_form = MessageFilterForm(data, language=language)
    if filter_form.is_valid():
        return {
            'sort_by': filter_form.cleaned_data['sort_by'],
            'company': filter_form.cleaned_data['company'],
        }
    return {
        'sort_by': MessageFilterForm.SORT_NEWEST,
        'company': MessageFilterForm.COMPANY_ALL,
    }


def build_filter_form(
    request: HttpRequest,
    language: str,
    *,
    initial_data: dict[str, str],
) -> MessageFilterForm:
    data = request.GET if request.method == 'GET' else request.POST
    if data and ('sort_by' in data or 'company' in data):
        form = MessageFilterForm(data, language=language)
        if form.is_valid():
            return form
    return MessageFilterForm(initial=initial_data, language=language)


def handle_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
    id_list = [int(value) for value in ids]
    status_actions: dict[str, tuple[str, str, str]] = {
        MessageBulkActionForm.ACTION_MARK_NEW: (
            ContactMessage.STATUS_NEW,
            'Zaznaczone wiadomości oznaczono jako nowe.',
            'Selected messages marked as new.',
        ),
        MessageBulkActionForm.ACTION_MARK_IN_PROGRESS: (
            ContactMessage.STATUS_IN_PROGRESS,
            'Zaznaczone wiadomości oznaczono jako w trakcie.',
            'Selected messages marked as in progress.',
        ),
        MessageBulkActionForm.ACTION_MARK_READY: (
            ContactMessage.STATUS_READY,
            'Zaznaczone wiadomości oznaczono jako gotowe.',
            'Selected messages marked as ready.',
        ),
    }

    success_message: str | None = None

    if action in status_actions:
        status, message_pl, message_en = status_actions[action]
        message_service.update_messages_status(id_list, status=status)
        log_bulk_action(
            AdminActivityLog.ACTION_STATUS_CHANGE,
            id_list,
            description=f'Status updated to {status}',
        )
        success_message = message_pl if lang == 'pl' else message_en
    elif action == MessageBulkActionForm.ACTION_DELETE:
        message_service.delete_messages(id_list)
        log_bulk_action(
            AdminActivityLog.ACTION_DELETE,
            id_list,
            description='Moved to trash',
        )
        success_message = (
            'Zaznaczone wiadomości przeniesiono do kosza.'
            if lang == 'pl'
            else 'Selected messages moved to trash.'
        )

    if success_message:
        messages.success(request, success_message, extra_tags='admin')


def handle_trash_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
    action_handlers: dict[str, tuple[Callable[[Iterable[int]], None], str, str]] = {
        TrashActionForm.ACTION_RESTORE: (
            message_service.restore_messages,
            'Wybrane wiadomości przywrócono.',
            'Selected messages restored.',
        ),
        TrashActionForm.ACTION_DELETE: (
            lambda message_ids: message_service.purge_messages(message_ids),
            'Wybrane wiadomości usunięto bezpowrotnie.',
            'Selected messages permanently deleted.',
        ),
        TrashActionForm.ACTION_EMPTY: (
            lambda _message_ids: message_service.purge_messages(),
            'Kosz opróżniono.',
            'Trash emptied.',
        ),
    }

    id_list = [int(value) for value in ids]
    handler = action_handlers.get(action)
    if not handler:
        return

    func, message_pl, message_en = handler
    func(id_list)
    if action == TrashActionForm.ACTION_RESTORE:
        log_bulk_action(
            AdminActivityLog.ACTION_RESTORE,
            id_list,
            description='Restored from trash',
        )
    elif action == TrashActionForm.ACTION_DELETE:
        log_bulk_action(
            AdminActivityLog.ACTION_PURGE,
            id_list,
            description='Permanently deleted',
        )
    elif action == TrashActionForm.ACTION_EMPTY:
        log_action(AdminActivityLog.ACTION_PURGE, description='Emptied trash bin')

    messages.success(request, message_pl if lang == 'pl' else message_en, extra_tags='admin')


def localise_action_choices(form: MessageBulkActionForm, lang: str) -> None:
    if lang == 'pl':
        form.fields['action'].choices = [
            (MessageBulkActionForm.ACTION_MARK_NEW, 'Oznacz jako nowe'),
            (MessageBulkActionForm.ACTION_MARK_IN_PROGRESS, 'Oznacz jako w trakcie'),
            (MessageBulkActionForm.ACTION_MARK_READY, 'Oznacz jako gotowe'),
            (MessageBulkActionForm.ACTION_DELETE, 'Usuń'),
        ]
    else:
        form.fields['action'].choices = [
            (MessageBulkActionForm.ACTION_MARK_NEW, 'Mark as new'),
            (MessageBulkActionForm.ACTION_MARK_IN_PROGRESS, 'Mark as in progress'),
            (MessageBulkActionForm.ACTION_MARK_READY, 'Mark as ready'),
            (MessageBulkActionForm.ACTION_DELETE, 'Delete'),
        ]


def serialise_attachment(attachment: ContactAttachment) -> dict[str, str | int]:
    return {
        'id': attachment.id,
        'name': attachment.original_name or attachment.file.name,
        'url': attachment.file.url,
        'content_type': attachment.content_type,
        'size': attachment.size,
    }


def serialise_client_message(
    message: ContactMessage,
    *,
    language: str,
) -> dict[str, object]:
    status_choices = status_options(language)
    status_lookup = {item['value']: item for item in status_choices}
    company_lookup = company_labels(language)
    status_info = status_lookup.get(
        message.status,
        {'label': message.status, 'badge': 'badge--info'},
    )
    created_at = timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M')
    return {
        'id': message.id,
        'full_name': message.full_name,
        'phone': message.phone,
        'email': message.email,
        'company': message.company,
        'company_name': message.company_name,
        'company_label': company_lookup.get(message.company, message.company),
        'message': message.message,
        'status': message.status,
        'status_label': status_info.get('label', message.status),
        'status_badge': status_info.get('badge', 'badge--info'),
        'created_at': created_at,
        'final_changes': message.final_changes,
        'final_response': message.final_response,
        'attachments': [serialise_attachment(att) for att in message.attachments.all()],
        'is_editable': message.status == ContactMessage.STATUS_NEW,
        'access_enabled': message.access_enabled,
    }
