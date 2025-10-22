from __future__ import annotations

import json
import logging
import math
import smtplib
from datetime import timedelta
from typing import Callable, Iterable
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    ContactForm,
    DownloadMessagesForm,
    EmailForm,
    LoginForm,
    MessageBulkActionForm,
    MessageFilterForm,
    MessageUpdateForm,
    TrashActionForm,
    UserMessageUpdateForm,
)
from .models import ContactMessage
from .services import messages as message_service
from .services.pdf_service import build_messages_pdf
from .services.email_service import (
    send_company_notification,
    send_contact_email,
    send_email_with_attachment,
)
from .utils import get_language
# Глобальные словари для учёта попыток
failed_attempts = {}
blocked_ips = {}

logger = logging.getLogger(__name__)



@require_http_methods(['GET', 'POST'])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None, language=lang)
    success_message = request.session.pop('contact_success', None)

    throttle_seconds = getattr(settings, 'CONTACT_FORM_THROTTLE_SECONDS', 30)
    form_valid = False
    throttle_error = False
    submission_timestamp: float | None = None

    if request.method == 'POST':
        form_valid = form.is_valid()
        submission_timestamp = timezone.now().timestamp()
        last_submission_raw = request.session.get('contact_last_submission')
        try:
            last_submission_ts = float(last_submission_raw)
        except (TypeError, ValueError):
            last_submission_ts = None

        if last_submission_ts is not None and submission_timestamp is not None:
            elapsed = submission_timestamp - last_submission_ts
            if elapsed < throttle_seconds:
                remaining_seconds = max(1, int(math.ceil(throttle_seconds - elapsed)))
                if lang == 'pl':
                    error_message = f'Proszę poczekać {remaining_seconds} s przed ponownym wysłaniem formularza.'
                else:
                    error_message = f'Please wait {remaining_seconds} s before submitting the form again.'
                form.add_error(None, error_message)
                throttle_error = True

    if request.method == 'POST' and form_valid and not throttle_error:
        payload = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "phone": form.cleaned_data["phone"],
            "email": form.cleaned_data["email"],
            "company": form.cleaned_data["company"],
            "message": form.cleaned_data["message"],
        }
        message = message_service.add_message(**payload)
        try:
            if settings.SMTP_USER:
                send_contact_email(form.cleaned_data['email'], message)
                notification_link = request.build_absolute_uri(reverse('contact:panel'))
                send_company_notification(message, link=notification_link)
        except smtplib.SMTPException:
            logger.exception('Failed to send contact form emails')
            message.delete()
            if lang == 'pl':
                error_text = 'Nie udało się wysłać wiadomości e-mail. Spróbuj ponownie później.'
            else:
                error_text = 'Unable to send the email right now. Please try again later.'
            form.add_error(None, error_text)
        else:
            _remember_user_message(request, message.id)
            if submission_timestamp is not None:
                request.session['contact_last_submission'] = submission_timestamp
            success_message = (
                'Wiadomość została wysłana. Zostanie przetworzona w ciągu 48 godzin, po czym się z Tobą skontaktujemy.'
                if lang == 'pl'
                else 'Your request has been sent. We will process it within 48 hours and contact you afterwards.'
            )
            messages.success(request, success_message)
            request.session['contact_success'] = success_message
            return redirect(f"{reverse('contact:index')}?lang={lang}")

    context = {
        'form': form,
        'lang': lang,
        'success_message': success_message,
    }
    return render(request, 'contact/index.html', context)


@require_http_methods(['GET', 'POST'])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = LoginForm(request.POST or None)
    ip = request.META.get('REMOTE_ADDR', 'unknown')

    # Проверка блокировки
    blocked = False
    time_left = None

    if ip in blocked_ips:
        if timezone.now() < blocked_ips[ip]:
            blocked = True
            # Вычисляем оставшееся время блокировки
            remaining_time = blocked_ips[ip] - timezone.now()
            total_seconds = int(remaining_time.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            time_left = f"{minutes:02d}:{seconds:02d}"
        else:
            # Сбрасываем, если время истекло
            blocked_ips.pop(ip, None)
            failed_attempts[ip] = 0

    # Обработка POST-запроса
    if request.method == 'POST' and not blocked and form.is_valid():
        if form.cleaned_data['password'] == settings.ADMIN_PASSWORD:
            # Успешный вход
            request.session['logged_in'] = True
            failed_attempts[ip] = 0
            return redirect('contact:panel')
        else:
            # Неверный пароль
            failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
            if failed_attempts[ip] >= 5:
                # Блокируем на 5 минут
                blocked_ips[ip] = timezone.now() + timedelta(minutes=5)
                blocked = True
                remaining_time = blocked_ips[ip] - timezone.now()
                total_seconds = int(remaining_time.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                time_left = f"{minutes:02d}:{seconds:02d}"
            else:
                # Показываем сколько попыток осталось
                error_message = (
                    f"Nieprawidłowe hasło! Pozostało prób: {5 - failed_attempts[ip]}"
                    if lang == 'pl'
                    else f"Wrong password! Attempts left: {5 - failed_attempts[ip]}"
                )
                form.add_error('password', error_message)
                if 'logged_in' in request.session:
                 del request.session['logged_in']

    return render(
        request,
        'contact/admin_login.html',
        {
            'form': form,
            'lang': lang,
            'blocked': blocked,
            'time_left': time_left,
        },
    )


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    request.session.flush()
    return redirect(f"{reverse('contact:index')}?lang={lang}")


@require_http_methods(['GET', 'POST'])
def panel(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    if not request.session.get('logged_in'):
        return redirect(f"{reverse('contact:login')}?lang={lang}")

    filter_data = _resolve_filter_data(request, lang)
    sort_by = filter_data["sort_by"]
    company_filter = filter_data["company"]

    queryset = message_service.get_messages(sort_by=sort_by, company=company_filter)
    deleted_queryset = message_service.get_deleted_messages()

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page') or request.POST.get('page') or 1
    page_obj = paginator.get_page(page_number)

    choices = [(str(message.id), f"#{message.id}") for message in page_obj.object_list]
    deleted_choices = [
        (str(message.id), f"#{message.id} · {message.email}") for message in deleted_queryset
    ]

    action_form = MessageBulkActionForm(request.POST or None, message_choices=choices)
    _localise_action_choices(action_form, lang)
    email_form = EmailForm()
    trash_form = TrashActionForm(message_choices=deleted_choices, language=lang)
    download_choices_raw = list(queryset.values_list('id', 'email'))
    download_choices = [
        (str(message_id), f"#{message_id} · {email}")
        for message_id, email in download_choices_raw
    ]
    download_form = DownloadMessagesForm(message_choices=download_choices, language=lang)
    filter_form = _build_filter_form(request, lang, initial_data=filter_data)

    if request.method == 'POST':
        form_name = request.POST.get('form_name')
        if form_name == 'bulk':
            action_form = MessageBulkActionForm(request.POST, message_choices=choices)
            _localise_action_choices(action_form, lang)
            if action_form.is_valid():
                ids = [int(pk) for pk in action_form.cleaned_data['selected']]
                _handle_action(action_form.cleaned_data['action'], ids, lang, request)
                return redirect(
                    _panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
        elif form_name == 'trash':
            trash_form = TrashActionForm(request.POST, message_choices=deleted_choices, language=lang)
            if trash_form.is_valid():
                ids = [int(pk) for pk in trash_form.cleaned_data['selected']]
                _handle_trash_action(trash_form.cleaned_data['action'], ids, lang, request)
                return redirect(
                    _panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
        elif form_name == 'download':
            download_form = DownloadMessagesForm(
                request.POST,
                message_choices=download_choices,
                language=lang,
            )
            if download_form.is_valid():
                ids = [int(pk) for pk in download_form.cleaned_data['messages']]
                fields = download_form.cleaned_data['fields']
                selected_messages = message_service.get_messages(
                    sort_by=sort_by,
                    company=company_filter,
                ).filter(id__in=ids)
                pdf_bytes = build_messages_pdf(selected_messages, fields=fields, language=lang)
                filename = timezone.localtime().strftime('requests_%Y%m%d_%H%M%S.pdf')
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            email_form = EmailForm(request.POST, request.FILES)
            if email_form.is_valid():
                file = request.FILES.get('attachment')
                send_email_with_attachment(
                    to_email=email_form.cleaned_data['to_email'],
                    subject=email_form.cleaned_data['subject'],
                    body=email_form.cleaned_data['body'],
                    attachment=file,
                    filename=file.name if file else None,
                )
                return redirect(
                    _panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )

    download_fields_total = len(download_form.fields['fields'].choices)
    selected_download_ids: list[str] = []
    if download_form.is_bound:
        raw_ids = download_form.data.getlist('messages')
        selected_download_ids = list(dict.fromkeys(raw_ids))

    company_options = _company_options(lang)
    status_options = _status_options(lang)
    status_meta = {item["value"]: {"label": item["label"], "badge": item["badge"]} for item in status_options}

    if lang == 'pl':
        detail_error_message = 'Nie udało się pobrać danych zgłoszenia.'
        update_error_message = 'Nie udało się zapisać zmian. Popraw błędy i spróbuj ponownie.'
    else:
        detail_error_message = 'Unable to load request data.'
        update_error_message = 'Could not save changes. Please fix the errors and try again.'

    context = {
        'lang': lang,
        'messages_page': page_obj,
        'paginator': paginator,
        'page_range': list(paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)),
        'deleted_messages': deleted_queryset,
        'action_form': action_form,
        'email_form': email_form,
        'trash_form': trash_form,
        'download_form': download_form,
        'filter_form': filter_form,
        'current_page': page_obj.number,
        'current_sort': sort_by,
        'current_company': company_filter,
        'download_has_choices': bool(download_choices),
        'download_fields_total': download_fields_total,
        'selected_download_ids': selected_download_ids,
        'company_options': company_options,
        'status_options': status_options,
        'status_meta_json': json.dumps(status_meta),
        'request_detail_error_message': detail_error_message,
        'request_update_error_message': update_error_message,
    }
    return render(request, 'contact/admin_panel.html', context)


@require_http_methods(['GET'])
def user_requests(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    stored_ids = _get_user_message_ids(request)
    queryset = (
        ContactMessage.objects.filter(id__in=stored_ids, is_deleted=False)
        .order_by('-created_at')
    )

    status_options = _status_options(lang)
    status_lookup = {item['value']: item for item in status_options}
    company_labels = _company_labels(lang)

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

    _store_user_message_ids(request, valid_ids)

    status_meta = {
        item['value']: {"label": item['label'], "badge": item['badge']} for item in status_options
    }

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
        'company_options': _company_options(lang),
        'detail_error_message': detail_error_message,
        'update_error_message': update_error_message,
        'delete_confirm_message': delete_confirm_message,
    }
    return render(request, 'contact/user_requests.html', context)


@require_http_methods(['GET'])
def user_message_detail(request: HttpRequest, message_id: int) -> JsonResponse:
    if not _user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    language = get_language(request)
    status_options = _status_options(language)
    status_lookup = {item['value']: item for item in status_options}
    company_labels = _company_labels(language)

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
    }
    return JsonResponse(data)


@require_POST
def user_update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not _user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    language = get_language(request)
    form = UserMessageUpdateForm(request.POST, instance=message)
    if form.is_valid():
        updated_message = form.save()
        status_options = _status_options(language)
        status_lookup = {item['value']: item for item in status_options}
        company_labels = _company_labels(language)
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
        }
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)


@require_POST
def user_delete_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not _user_can_access_message(request, message_id):
        return JsonResponse({'error': 'not_found'}, status=404)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    message.is_deleted = True
    message.save(update_fields=['is_deleted'])
    _remove_user_message(request, message_id)
    return JsonResponse({'success': True})


@require_http_methods(['GET'])
def message_detail(request: HttpRequest, message_id: int) -> JsonResponse:
    if not request.session.get('logged_in'):
        return JsonResponse({'error': 'unauthorized'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    language = get_language(request)
    created_at = timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M')
    status_options = _status_options(language)
    status_labels = {item['value']: item['label'] for item in status_options}

    data = {
        'id': message.id,
        'first_name': message.first_name,
        'last_name': message.last_name,
        'phone': message.phone,
        'email': message.email,
        'company': message.company,
        'message': message.message,
        'status': message.status,
        'status_label': status_labels.get(message.status, message.status),
        'created_at': created_at,
        'final_changes': message.final_changes,
        'final_response': message.final_response,
    }
    return JsonResponse(data)


@require_POST
def update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    if not request.session.get('logged_in'):
        return JsonResponse({'error': 'unauthorized'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    language = get_language(request)
    form = MessageUpdateForm(request.POST, instance=message)
    if form.is_valid():
        updated_message = form.save()
        status_options = _status_options(language)
        status_lookup = {item['value']: item for item in status_options}
        status_info = status_lookup.get(updated_message.status, {'label': updated_message.status, 'badge': 'badge--info'})
        data = {
            'id': updated_message.id,
            'first_name': updated_message.first_name,
            'last_name': updated_message.last_name,
            'phone': updated_message.phone,
            'email': updated_message.email,
            'company': updated_message.company,
            'message': updated_message.message,
            'status': updated_message.status,
            'status_label': status_info['label'],
            'status_badge': status_info['badge'],
            'created_at': timezone.localtime(updated_message.created_at).strftime('%Y-%m-%d %H:%M'),
            'final_changes': updated_message.final_changes,
            'final_response': updated_message.final_response,
        }
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)


def _remember_user_message(request: HttpRequest, message_id: int) -> None:
    stored_ids = _get_user_message_ids(request)
    if message_id not in stored_ids:
        stored_ids.append(message_id)
    _store_user_message_ids(request, stored_ids)


def _store_user_message_ids(request: HttpRequest, message_ids: list[int]) -> None:
    unique_ids = list(dict.fromkeys(message_ids))
    request.session['user_message_ids'] = unique_ids


def _get_user_message_ids(request: HttpRequest) -> list[int]:
    raw_ids = request.session.get('user_message_ids', [])
    result: list[int] = []
    for value in raw_ids:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _remove_user_message(request: HttpRequest, message_id: int) -> None:
    remaining = [mid for mid in _get_user_message_ids(request) if mid != int(message_id)]
    _store_user_message_ids(request, remaining)


def _user_can_access_message(request: HttpRequest, message_id: int) -> bool:
    return int(message_id) in _get_user_message_ids(request)


def _panel_redirect_url(
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


def _company_options(language: str) -> list[dict[str, str]]:
    labels = _company_labels(language)
    return [
        {
            'value': value,
            'label': labels.get(value, label),
        }
        for value, label in ContactForm.COMPANY_CHOICES
    ]


def _company_labels(language: str) -> dict[str, str]:
    if language == 'pl':
        return {value: label for value, label in ContactForm.COMPANY_CHOICES}
    return {
        'firma1': 'Company 1',
        'firma2': 'Company 2',
        'firma3': 'Company 3',
        'inna': 'Other',
    }


def _status_options(language: str) -> list[dict[str, str]]:
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


def _resolve_filter_data(request: HttpRequest, language: str) -> dict[str, str]:
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


def _build_filter_form(
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


def _handle_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
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
        message_service.update_messages_status(ids, status=status)
        success_message = message_pl if lang == 'pl' else message_en
    elif action == MessageBulkActionForm.ACTION_DELETE:
        message_service.delete_messages(ids)
        success_message = (
            'Zaznaczone wiadomości przeniesiono do kosza.'
            if lang == 'pl'
            else 'Selected messages moved to trash.'
        )

    if success_message:
        messages.success(request, success_message)


def _handle_trash_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
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

    handler = action_handlers.get(action)
    if not handler:
        return

    func, message_pl, message_en = handler
    func(ids)
    messages.success(request, message_pl if lang == 'pl' else message_en)


def _localise_action_choices(form: MessageBulkActionForm, lang: str) -> None:
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
