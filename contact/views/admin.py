from __future__ import annotations

import json

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from ..forms import (
    DownloadMessagesForm,
    EmailForm,
    MessageBulkActionForm,
    MessageFilterForm,
    MessageUpdateForm,
    TrashActionForm,
)
from ..models import ContactMessage
from ..services import messages as message_service
from ..services.email_service import send_email_with_attachment
from ..services.pdf_service import build_messages_pdf
from ..utils import get_language
from . import helpers


@require_http_methods(["GET", "POST"])
def admin_panel(request: HttpRequest) -> HttpResponse:
    if not request.session.get('logged_in'):
        return redirect('contact:login')

    lang = get_language(request)

    filter_data = helpers.resolve_filter_data(request, lang)
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
    helpers.localise_action_choices(action_form, lang)
    email_form = EmailForm(request.POST or None, request.FILES or None)
    trash_form = TrashActionForm(request.POST or None, message_choices=deleted_choices, language=lang)
    download_choices_raw = list(queryset.values_list('id', 'email'))
    download_choices = [
        (str(message_id), f"#{message_id} · {email}")
        for message_id, email in download_choices_raw
    ]
    download_form = DownloadMessagesForm(
        request.POST or None,
        message_choices=download_choices,
        language=lang,
    )
    filter_form = helpers.build_filter_form(request, lang, initial_data=filter_data)

    if request.method == 'POST':
        form_name = (request.POST.get('form_name') or '').strip()
        if form_name == 'bulk':
            action_form, response = _handle_bulk_form(
                request,
                lang,
                choices,
                page_obj,
                sort_by,
                company_filter,
            )
            if response:
                return response
        elif form_name == 'trash':
            trash_form, response = _handle_trash_form(
                request,
                lang,
                deleted_choices,
                page_obj,
                sort_by,
                company_filter,
            )
            if response:
                return response
        elif form_name == 'download':
            download_form, response = _handle_download_form(
                request,
                lang,
                download_choices,
                sort_by,
                company_filter,
            )
            if response:
                return response
        else:
            email_form, response = _handle_email_form(
                request,
                lang,
                page_obj,
                sort_by,
                company_filter,
            )
            if response:
                return response

    download_fields_total = len(download_form.fields['fields'].choices)
    selected_download_ids: list[str] = []
    if download_form.is_bound:
        raw_ids = download_form.data.getlist('messages')
        selected_download_ids = list(dict.fromkeys(raw_ids))

    company_options = helpers.company_options(lang)
    status_options = helpers.status_options(lang)
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


def _handle_bulk_form(
    request: HttpRequest,
    lang: str,
    choices: list[tuple[str, str]],
    page_obj,
    sort_by: str | None,
    company_filter: str | None,
):
    form = MessageBulkActionForm(request.POST, message_choices=choices)
    helpers.localise_action_choices(form, lang)
    if form.is_valid():
        ids = [int(pk) for pk in form.cleaned_data['selected']]
        helpers.handle_action(form.cleaned_data['action'], ids, lang, request)
        return form, redirect(
            helpers.panel_redirect_url(
                lang,
                page_obj.number,
                sort_by=sort_by,
                company=company_filter,
            )
        )
    return form, None


def _handle_trash_form(
    request: HttpRequest,
    lang: str,
    deleted_choices: list[tuple[str, str]],
    page_obj,
    sort_by: str | None,
    company_filter: str | None,
):
    form = TrashActionForm(request.POST, message_choices=deleted_choices, language=lang)
    if form.is_valid():
        ids = [int(pk) for pk in form.cleaned_data['selected']]
        helpers.handle_trash_action(form.cleaned_data['action'], ids, lang, request)
        return form, redirect(
            helpers.panel_redirect_url(
                lang,
                page_obj.number,
                sort_by=sort_by,
                company=company_filter,
            )
        )
    return form, None


def _handle_download_form(
    request: HttpRequest,
    lang: str,
    download_choices: list[tuple[str, str]],
    sort_by: str | None,
    company_filter: str | None,
):
    form = DownloadMessagesForm(
        request.POST,
        message_choices=download_choices,
        language=lang,
    )
    if form.is_valid():
        ids = [int(pk) for pk in form.cleaned_data['messages']]
        fields = form.cleaned_data['fields']
        selected_messages = message_service.get_messages(
            sort_by=sort_by,
            company=company_filter,
        ).filter(id__in=ids)
        pdf_bytes = build_messages_pdf(selected_messages, fields=fields, language=lang)
        filename = timezone.localtime().strftime('requests_%Y%m%d_%H%M%S.pdf')
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return form, response
    return form, None


def _handle_email_form(
    request: HttpRequest,
    lang: str,
    page_obj,
    sort_by: str | None,
    company_filter: str | None,
):
    form = EmailForm(request.POST, request.FILES or None)
    if form.is_valid():
        file = request.FILES.get('attachment')
        send_email_with_attachment(
            to_email=form.cleaned_data['to_email'],
            subject=form.cleaned_data['subject'],
            body=form.cleaned_data['body'],
            attachment=file,
            filename=file.name if file else None,
        )
        return form, redirect(
            helpers.panel_redirect_url(
                lang,
                page_obj.number,
                sort_by=sort_by,
                company=company_filter,
            )
        )
    return form, None


@require_http_methods(["GET"])
def message_detail(request: HttpRequest, message_id: int) -> JsonResponse:
    if not request.session.get('logged_in'):
        return JsonResponse({'error': 'unauthorized'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    language = get_language(request)
    created_at = timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M')
    status_options = helpers.status_options(language)
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
        'access_token_hash': message.access_token_hash,
        'access_enabled': message.access_enabled,
        'attachments': [helpers.serialise_attachment(att) for att in message.attachments.all()],
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
        status_options = helpers.status_options(language)
        status_lookup = {item['value']: item for item in status_options}
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
            'message': updated_message.message,
            'status': updated_message.status,
            'status_label': status_info['label'],
            'status_badge': status_info['badge'],
            'created_at': timezone.localtime(updated_message.created_at).strftime('%Y-%m-%d %H:%M'),
            'final_changes': updated_message.final_changes,
            'final_response': updated_message.final_response,
            'access_token_hash': updated_message.access_token_hash,
            'access_enabled': updated_message.access_enabled,
            'attachments': [helpers.serialise_attachment(att) for att in updated_message.attachments.all()],
        }
        return JsonResponse(data)

    return JsonResponse({'errors': form.errors}, status=400)
