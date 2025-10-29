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
from ..models import ContactMessage
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
    status_options = helpers.status_options(language)
    status_lookup = {item['value']: item for item in status_options}
    company_labels = helpers.company_labels(language)

    data = {
        'id': message.id,
        'first_name': message.first_name,
        'last_name': message.last_name,
        'phone': message.phone,
        'email': message.email,
        'company': message.company,
        'company_label': company_labels.get(message.company, message.company),
        'message': message.message,
        'status': message.status,
        'status_label': status_lookup.get(message.status, {}).get('label', message.status),
        'status_badge': status_lookup.get(message.status, {}).get('badge', 'badge--info'),
        'created_at': timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M'),
        'final_changes': message.final_changes,
        'final_response': message.final_response,
        'attachments': [helpers.serialise_attachment(att) for att in message.attachments.all()],
    }
    return JsonResponse(data)


@require_POST
def user_update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not helpers.user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(
        ContactMessage.objects.filter(pk=message_id, is_deleted=False, access_enabled=True)
        .filter(Q(access_token_expires_at__isnull=True) | Q(access_token_expires_at__gt=timezone.now()))
    )
    language = get_language(request)
    form = UserMessageUpdateForm(request.POST, request.FILES, instance=message)
    if form.is_valid():
        updated_message = form.save()
        attachments = form.cleaned_data.get('attachments') or []
        if attachments:
            message_service.add_attachments(updated_message, attachments)
        status_options = helpers.status_options(language)
        status_lookup = {item['value']: item for item in status_options}
        company_labels = helpers.company_labels(language)
        status_info = status_lookup.get(
            updated_message.status,
            {'label': updated_message.status, 'badge': 'badge--info'},
        )
        data = {
            'id': updated_message.id,
            'first_name': updated_message.first_name,
            'last_name': updated_message.last_name,
            'phone': updated_message.phone,
            'email': updated_message.email,
            'company': updated_message.company,
            'company_label': company_labels.get(updated_message.company, updated_message.company),
            'message': updated_message.message,
            'status': updated_message.status,
            'status_label': status_info['label'],
            'status_badge': status_info['badge'],
            'created_at': timezone.localtime(updated_message.created_at).strftime('%Y-%m-%d %H:%M'),
            'final_changes': updated_message.final_changes,
            'final_response': updated_message.final_response,
            'attachments': [helpers.serialise_attachment(att) for att in updated_message.attachments.all()],
        }
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)


@require_POST
def user_delete_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not helpers.user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    message.is_deleted = True
    message.save(update_fields=['is_deleted'])
    helpers.remove_user_message(request, message_id)
    return JsonResponse({'success': True})
