from __future__ import annotations

import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Q

from ..forms import RequestAccessForm, UserMessageUpdateForm
from ..models import ClientChangeLog, ContactMessage
from ..services import messages as message_service
from ..utils import get_language
from . import helpers


@require_http_methods(["GET", "POST"])
def access_portal(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    stored_ids = helpers.get_user_message_ids(request)
    form = RequestAccessForm(request.POST or None, stored_ids=stored_ids, language=lang)

    if request.method == 'POST' and form.is_valid():
        message_id = form.cleaned_data['request_id']
        token = form.cleaned_data['access_token']
        message = ContactMessage.objects.filter(id=message_id, is_deleted=False).first()
        if not message or not message.access_enabled:
            error = (
                'Nie znaleziono zgłoszenia o podanym numerze.'
                if lang == 'pl'
                else 'No request with this number could be found.'
            )
            form.add_error('request_id', error)
        elif message.is_access_token_expired:
            error = (
                'Token wygasł. Poproś o nowy dostęp.'
                if lang == 'pl'
                else 'The access token has expired. Please request new access.'
            )
            form.add_error('access_token', error)
        elif not message.verify_access_token(token):
            error = (
                'Token nie pasuje do zgłoszenia.'
                if lang == 'pl'
                else 'The token does not match this request.'
            )
            form.add_error('access_token', error)
        else:
            helpers.remember_user_message(request, message.id)
            success = (
                'Dostęp przyznany. Możesz teraz zarządzać zgłoszeniem.'
                if lang == 'pl'
                else 'Access granted. You can now manage the request.'
            )
            messages.success(request, success)
            return redirect(f"{reverse('contact:user_requests')}?lang={lang}")

    context = {
        'lang': lang,
        'form': form,
        'stored_ids': stored_ids,
    }
    return render(request, 'contact/request_portal.html', context)


@require_POST
def restore_access(request: HttpRequest) -> JsonResponse:
    language = get_language(request)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        payload = request.POST
    form = RequestAccessForm(payload, language=language)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    message_id = form.cleaned_data['request_id']
    token = form.cleaned_data['access_token']
    message = ContactMessage.objects.filter(id=message_id, is_deleted=False).first()
    if not message or not message.access_enabled:
        error = (
            'Nie znaleziono zgłoszenia o podanym numerze.'
            if language == 'pl'
            else 'No request with this number could be found.'
        )
        return JsonResponse({'errors': {'request_id': [error]}}, status=400)
    if message.is_access_token_expired:
        error = (
            'Token wygasł. Poproś o nowy dostęp.'
            if language == 'pl'
            else 'The access token has expired. Please request new access.'
        )
        return JsonResponse({'errors': {'access_token': [error]}}, status=400)
    if not message.verify_access_token(token):
        error = (
            'Token nie pasuje do zgłoszenia.'
            if language == 'pl'
            else 'The token does not match this request.'
        )
        return JsonResponse({'errors': {'access_token': [error]}}, status=400)

    helpers.remember_user_message(request, message.id)
    success_message = (
        'Dostęp przywrócono. Możesz kontynuować edycję zgłoszenia.'
        if language == 'pl'
        else 'Access restored. You can continue working on your request.'
    )
    return JsonResponse({'success': True, 'message_id': message.id, 'message': success_message})


@require_http_methods(["GET"])
def user_requests(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    stored_ids = helpers.get_user_message_ids(request)
    queryset = (
        ContactMessage.objects.filter(id__in=stored_ids, is_deleted=False, access_enabled=True)
        .filter(Q(access_token_expires_at__isnull=True) | Q(access_token_expires_at__gt=timezone.now()))
        .order_by('-created_at')
    )

    status_options = helpers.status_options(lang)
    status_lookup = {item['value']: item for item in status_options}
    company_labels = helpers.company_labels(lang)

    request_cards: list[dict[str, str]] = []
    valid_ids: list[int] = []
    for message in queryset:
        valid_ids.append(message.id)
        status_info = status_lookup.get(
            message.status,
            {'label': message.status, 'badge': 'badge--info'},
        )
        request_cards.append(
            {
                'id': message.id,
                'created_at': timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M'),
                'status': message.status,
                'status_label': status_info['label'],
                'status_badge': status_info['badge'],
                'company_label': company_labels.get(message.company, message.company),
                'company_name': message.company_name,
                'message_preview': message.message,
            }
        )

    helpers.store_user_message_ids(request, valid_ids)

    status_meta = {
        item['value']: {"label": item['label'], "badge": item['badge']} for item in status_options
    }

    allowed_types = [
        content_type.strip()
        for content_type in getattr(settings, 'ATTACH_ALLOWED_TYPES', [])
        if content_type.strip()
    ]

    if lang == 'pl':
        detail_error_message = 'Nie udało się pobrać danych zgłoszenia.'
        update_error_message = 'Nie udało się zapisać zmian. Popraw błędy i spróbuj ponownie.'
        delete_confirm_message = 'Czy na pewno chcesz usunąć to zgłoszenie?'
    else:
        detail_error_message = 'Unable to load request details.'
        update_error_message = 'Could not save changes. Please fix the errors and try again.'
        delete_confirm_message = 'Are you sure you want to delete this request?'

    context = {
        'lang': lang,
        'request_cards': request_cards,
        'status_meta_json': json.dumps(status_meta),
        'company_options': helpers.company_options(lang),
        'detail_error_message': detail_error_message,
        'update_error_message': update_error_message,
        'delete_confirm_message': delete_confirm_message,
        'max_attachment_size': getattr(settings, 'ATTACH_MAX_SIZE_MB', 25),
        'allowed_attachment_types': allowed_types,
    }
    return render(request, 'contact/user_requests.html', context)


@require_http_methods(["GET"])
def user_message_detail(request: HttpRequest, message_id: int) -> JsonResponse:
    if not helpers.user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(
        ContactMessage.objects.filter(pk=message_id, is_deleted=False, access_enabled=True)
        .filter(Q(access_token_expires_at__isnull=True) | Q(access_token_expires_at__gt=timezone.now()))
    )
    language = get_language(request)
    data = helpers.serialise_client_message(message, language=language)
    return JsonResponse(data)


@require_POST
def user_update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not helpers.user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(
        ContactMessage.objects.filter(pk=message_id, is_deleted=False, access_enabled=True)
        .filter(Q(access_token_expires_at__isnull=True) | Q(access_token_expires_at__gt=timezone.now()))
    )
    if message.status != ContactMessage.STATUS_NEW:
        return JsonResponse({'error': 'locked'}, status=403)
    language = get_language(request)
    form = UserMessageUpdateForm(request.POST, request.FILES, instance=message)
    if form.is_valid():
        tracked_fields = {
            ClientChangeLog.FIELD_FULL_NAME,
            ClientChangeLog.FIELD_PHONE,
            ClientChangeLog.FIELD_EMAIL,
            ClientChangeLog.FIELD_COMPANY,
            ClientChangeLog.FIELD_COMPANY_NAME,
            ClientChangeLog.FIELD_MESSAGE,
        }
        changed_fields = [field for field in form.changed_data if field in tracked_fields]
        before_values = {field: getattr(message, field) for field in changed_fields}
        updated_message = form.save()
        attachments = form.cleaned_data.get('attachments') or []
        if attachments:
            message_service.add_attachments(updated_message, attachments)
        log_entries: list[ClientChangeLog] = []
        for field in changed_fields:
            previous = before_values.get(field, '') or ''
            current = getattr(updated_message, field) or ''
            if str(previous) == str(current):
                continue
            log_entries.append(
                ClientChangeLog(
                    message=updated_message,
                    field=field,
                    previous_value=str(previous),
                    new_value=str(current),
                )
            )
        if log_entries:
            ClientChangeLog.objects.bulk_create(log_entries)
        data = helpers.serialise_client_message(updated_message, language=language)
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)


@require_POST
def user_delete_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not helpers.user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    if message.status != ContactMessage.STATUS_NEW:
        return JsonResponse({'error': 'locked'}, status=403)
    message.is_deleted = True
    message.save(update_fields=['is_deleted'])
    helpers.remove_user_message(request, message_id)
    return JsonResponse({'success': True})
