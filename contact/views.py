from __future__ import annotations

import json
from typing import Iterable
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
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
)
from .models import ContactMessage
from .services import messages as message_service
from .services.pdf_service import build_messages_pdf
from .services.email_service import send_contact_email, send_email_with_attachment
from .utils import get_language


@require_http_methods(['GET', 'POST'])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None, language=lang)
    success_message = request.session.pop('contact_success', None)

    if request.method == 'POST' and form.is_valid():
        payload = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "phone": form.cleaned_data["phone"],
            "email": form.cleaned_data["email"],
            "company": form.cleaned_data["company"],
            "message": form.cleaned_data["message"],
        }
        message = message_service.add_message(**payload)
        if settings.SMTP_USER:
            send_contact_email(form.cleaned_data['email'], message)
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
    default_back_url = f"{reverse('contact:index')}?lang={lang}"

    def _sanitize_back_url(candidate: str | None) -> str | None:
        if not candidate:
            return None
        if url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return candidate
        return None

    back_url = (
        _sanitize_back_url(request.POST.get('next'))
        or _sanitize_back_url(request.GET.get('next'))
        or _sanitize_back_url(request.META.get('HTTP_REFERER'))
        or default_back_url
    )

    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['password'] == settings.ADMIN_PASSWORD:
            request.session['logged_in'] = True
            return redirect('contact:panel')
        error_message = 'Nieprawidłowe hasło!' if lang == 'pl' else 'Wrong password!'
        form.add_error('password', error_message)

    return render(
        request,
        'contact/admin_login.html',
        {
            'form': form,
            'lang': lang,
            'back_url': back_url,
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
                success_message = 'E-mail został wysłany.' if lang == 'pl' else 'Email sent.'
                messages.success(request, success_message)
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
        update_success_message = 'Zgłoszenie zostało zaktualizowane.'
        detail_error_message = 'Nie udało się pobrać danych zgłoszenia.'
        update_error_message = 'Nie udało się zapisać zmian. Popraw błędy i spróbuj ponownie.'
    else:
        update_success_message = 'Request updated successfully.'
        detail_error_message = 'Unable to load request data.'
        update_error_message = 'Could not save changes. Please fix the errors and try again.'

    panel_base_url = reverse('contact:panel')
    current_query_params = request.GET.copy()

    def _panel_lang_switch(target_lang: str) -> str:
        params = current_query_params.copy()
        params['lang'] = target_lang
        query_string = params.urlencode()
        return f"{panel_base_url}?{query_string}" if query_string else panel_base_url

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
        'request_update_success_message': update_success_message,
        'request_detail_error_message': detail_error_message,
        'request_update_error_message': update_error_message,
        'panel_lang_switch_pl': _panel_lang_switch('pl'),
        'panel_lang_switch_en': _panel_lang_switch('en'),
    }
    return render(request, 'contact/admin_panel.html', context)


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
        }
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)


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
    if language == 'pl':
        labels = {value: label for value, label in ContactForm.COMPANY_CHOICES}
    else:
        labels = {
            'firma1': 'Company 1',
            'firma2': 'Company 2',
            'firma3': 'Company 3',
            'inna': 'Other',
        }
    return [
        {
            'value': value,
            'label': labels.get(value, label),
        }
        for value, label in ContactForm.COMPANY_CHOICES
    ]


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
    if action == MessageBulkActionForm.ACTION_MARK_NEW:
        message_service.mark_messages_new(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako nowe.'
            if lang == 'pl'
            else 'Selected messages marked as new.'
        )
    elif action == MessageBulkActionForm.ACTION_MARK_IN_PROGRESS:
        message_service.mark_messages_in_progress(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako w trakcie.'
            if lang == 'pl'
            else 'Selected messages marked as in progress.'
        )
    elif action == MessageBulkActionForm.ACTION_MARK_READY:
        message_service.mark_messages_ready(ids)
        text = (
            'Zaznaczone wiadomości oznaczono jako gotowe.'
            if lang == 'pl'
            else 'Selected messages marked as ready.'
        )
    else:
        message_service.delete_messages(ids)
        text = (
            'Zaznaczone wiadomości przeniesiono do kosza.'
            if lang == 'pl'
            else 'Selected messages moved to trash.'
        )
    messages.success(request, text)


def _handle_trash_action(action: str, ids: Iterable[int], lang: str, request: HttpRequest) -> None:
    if action == TrashActionForm.ACTION_RESTORE:
        message_service.restore_messages(ids)
        text = (
            'Wybrane wiadomości przywrócono.'
            if lang == 'pl'
            else 'Selected messages restored.'
        )
    elif action == TrashActionForm.ACTION_DELETE:
        message_service.purge_messages(ids)
        text = (
            'Wybrane wiadomości usunięto bezpowrotnie.'
            if lang == 'pl'
            else 'Selected messages permanently deleted.'
        )
    else:
        message_service.purge_messages()
        text = (
            'Kosz opróżniono.'
            if lang == 'pl'
            else 'Trash emptied.'
        )
    messages.success(request, text)


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
