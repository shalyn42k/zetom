from __future__ import annotations

from typing import Iterable
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    ContactForm,
    DownloadMessagesForm,
    EmailForm,
    LoginForm,
    MessageBulkActionForm,
    MessageFilterForm,
    TrashActionForm,
)
from .services import messages as message_service
from .services.pdf_service import build_messages_pdf
from .services.email_service import send_contact_email, send_email_with_attachment
from .utils import get_language


@require_http_methods(['GET', 'POST'])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = message_service.add_message(**form.cleaned_data)
        if settings.SMTP_USER:
            send_contact_email(form.cleaned_data['email'], message)
        success_message = (
            'Wiadomość została wysłana. Skontaktujemy się w ciągu 24 godzin.'
            if lang == 'pl'
            else 'Message sent. We will get back to you within 24 hours.'
        )
        messages.success(request, success_message)
        return redirect(f"{reverse('contact:index')}?lang={lang}")

    context = {
        'form': form,
        'lang': lang,
    }
    return render(request, 'contact/index.html', context)


@require_http_methods(['GET', 'POST'])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['password'] == settings.ADMIN_PASSWORD:
            request.session['logged_in'] = True
            return redirect('contact:panel')
        error_message = 'Nieprawidłowe hasło!' if lang == 'pl' else 'Wrong password!'
        form.add_error('password', error_message)

    return render(request, 'contact/admin_login.html', {'form': form, 'lang': lang})


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
    }
    return render(request, 'contact/admin_panel.html', context)


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
