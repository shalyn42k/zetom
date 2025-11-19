from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import EmailValidator
from django.db import transaction
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
from ..forms import ContactForm
from ..models import AdminActivityLog, AdminUser, ClientChangeLog, ContactMessage
from ..services import messages as message_service
from ..services.activity_log import log_action
from ..services.email_service import (
    send_admin_user_credentials,
    send_email_with_attachment,
)
from ..services.pdf_service import build_messages_pdf
from ..utils import get_language
from . import helpers


def _serialise_admin_message(message: ContactMessage, language: str) -> dict:
    status_options = helpers.status_options(language)
    status_lookup = {item['value']: item for item in status_options}
    company_labels = helpers.company_labels(language)
    status_info = status_lookup.get(
        message.status,
        {'label': message.status, 'badge': 'badge--info'},
    )
    logs = ClientChangeLog.objects.filter(message=message).order_by('-changed_at', '-id')
    return {
        'id': message.id,
        'full_name': message.full_name,
        'phone': message.phone,
        'email': message.email,
        'company': message.company,
        'company_name': message.company_name,
        'company_label': company_labels.get(message.company, message.company),
        'message': message.message,
        'status': message.status,
        'status_label': status_info['label'],
        'status_badge': status_info['badge'],
        'created_at': timezone.localtime(message.created_at).strftime('%Y-%m-%d %H:%M'),
        'final_changes': message.final_changes,
        'final_response': message.final_response,
        'access_token_hash': message.access_token_hash,
        'access_enabled': message.access_enabled,
        'attachments': [helpers.serialise_attachment(att) for att in message.attachments.all()],
        'client_logs': [
            {
                'id': log.id,
                'field': log.field,
                'previous_value': log.previous_value,
                'new_value': log.new_value,
                'changed_at': timezone.localtime(log.changed_at).strftime('%Y-%m-%d %H:%M'),
                'is_reverted': log.is_reverted,
            }
            for log in logs
        ],
    }


def _get_admin_user(request: HttpRequest) -> AdminUser | None:
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return AdminUser.objects.get(id=user_id)
    except AdminUser.DoesNotExist:
        return None


def _can_access_message(admin_user: AdminUser | None, message: ContactMessage) -> bool:
    if not admin_user:
        return False
    if admin_user.level == AdminUser.LEVEL_DEPARTMENT:
        if not admin_user.department:
            return False
        return message.company == admin_user.department
    return True


@require_http_methods(["GET", "POST"])
def admin_panel(request: HttpRequest) -> HttpResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return redirect('contact:login')

    user_level = admin_user.level
    request.session['user_level'] = user_level
    request.session['user_email'] = admin_user.email
    request.session['user_id'] = admin_user.id
    request.session['user_department'] = admin_user.department
    readonly_mode = user_level == AdminUser.LEVEL_TESTER
    lang = get_language(request)

    user_department = (admin_user.department or "").strip()
    department_label = helpers.company_labels(lang).get(user_department, user_department or "")

    if user_level == AdminUser.LEVEL_DEPARTMENT:
        filter_data = helpers.resolve_filter_data(
            request,
            lang,
            company_choices=[(user_department, department_label)] if user_department else [],
            include_all=False,
        )
        sort_by = filter_data["sort_by"]
        company_filter = user_department or filter_data["company"]
        filter_data["company"] = company_filter
    else:
        filter_data = helpers.resolve_filter_data(request, lang)
        sort_by = filter_data["sort_by"]
        company_filter = filter_data["company"]

    if user_level == AdminUser.LEVEL_DEPARTMENT and not user_department:
        queryset = ContactMessage.objects.none()
        deleted_queryset = ContactMessage.objects.none()
    else:
        queryset = message_service.get_messages(sort_by=sort_by, company=company_filter)
        deleted_queryset = message_service.get_deleted_messages()
        if user_level == AdminUser.LEVEL_DEPARTMENT and user_department:
            queryset = queryset.filter(company=user_department)
            deleted_queryset = deleted_queryset.filter(company=user_department)

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
    if readonly_mode:
        action_form.fields['action'].disabled = True
        action_form.fields['selected'].disabled = True
    filter_form = helpers.build_filter_form(
        request,
        lang,
        initial_data=filter_data,
        company_choices=[(user_department, department_label)] if user_level == AdminUser.LEVEL_DEPARTMENT else None,
        include_all=user_level != AdminUser.LEVEL_DEPARTMENT,
    )

    if user_level == AdminUser.LEVEL_DEPARTMENT:
        filter_form.fields['company'].initial = user_department
        filter_form.fields['company'].widget.attrs['disabled'] = True

    if request.method == 'POST' and readonly_mode:
        return redirect(
            helpers.panel_redirect_url(
                lang,
                page_obj.number,
                sort_by=sort_by,
                company=company_filter,
            )
        )

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
    settings_departments_json = json.dumps(company_options)
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
        'user_level': user_level,
        'readonly_mode': readonly_mode,
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
        'settings_departments_json': settings_departments_json,
        'status_options': status_options,
        'status_meta_json': json.dumps(status_meta),
        'request_detail_error_message': detail_error_message,
        'request_update_error_message': update_error_message,
    }
    return render(request, 'contact/admin_panel.html', context)


def _serialise_admin_user(user: AdminUser) -> dict:
    return {
        'user_id': user.id,
        'email': user.email,
        'password_plaintext': user.reveal_plaintext_password() or '',
        'has_password': bool(user.password_ciphertext or user.password_hash),
        'level': user.level,
        'department': user.department,
    }


@require_http_methods(["GET", "POST"])
def admin_settings(request: HttpRequest) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorised'}, status=403)

    if admin_user.level != AdminUser.LEVEL_ADMIN:
        return JsonResponse({'error': 'forbidden'}, status=403)

    language = get_language(request)
    level_labels = {
        AdminUser.LEVEL_ADMIN: 'level1',
        AdminUser.LEVEL_DEPARTMENT: 'level2',
        AdminUser.LEVEL_TESTER: 'level3',
    }
    allowed_departments = {value for value, _ in AdminUser.DEPARTMENT_CHOICES}
    error_messages = {
        'invalid_payload': 'Nieprawidłowy format danych.' if language == 'pl' else 'Invalid payload.',
        'duplicate_user_id': 'Duplikat identyfikatora użytkownika.' if language == 'pl' else 'Duplicate user id detected.',
        'unknown_user_id': 'Nieznany użytkownik.' if language == 'pl' else 'Unknown user.',
        'email_required': 'Email jest wymagany.' if language == 'pl' else 'Email is required.',
        'email_invalid': 'Email jest nieprawidłowy.' if language == 'pl' else 'Email format is invalid.',
        'email_not_unique': 'Email musi być unikalny.' if language == 'pl' else 'Email must be unique.',
        'level_required': 'Poziom dostępu jest wymagany.' if language == 'pl' else 'Level of access is required.',
        'department_required': 'Departament jest wymagany dla level2.' if language == 'pl' else 'Department is required for level2 users.',
        'department_invalid': 'Nieprawidłowy departament.' if language == 'pl' else 'Invalid department.',
        'password_required': 'Hasło jest wymagane.' if language == 'pl' else 'Password is required.',
        'no_admin_left': 'Musi pozostać co najmniej jeden administrator level1.'
        if language == 'pl'
        else 'At least one level1 admin must remain.',
    }

    email_validator = EmailValidator(message=error_messages['email_invalid'])

    if request.method == 'GET':
        users = [_serialise_admin_user(user) for user in AdminUser.objects.all().order_by('id')]
        return JsonResponse({'users': users})

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        return JsonResponse({'errors': [error_messages['invalid_payload']]}, status=400)

    rows = payload.get('users', []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return JsonResponse({'errors': [error_messages['invalid_payload']]}, status=400)

    existing_users = {str(user.id): user for user in AdminUser.objects.all()}
    seen_ids: set[str] = set()
    planned_email_map: dict[str, str] = {}
    errors: list[str] = []

    def _error(code: str) -> None:
        errors.append(error_messages.get(code, code))

    # Basic row validation
    validated_rows: list[dict] = []
    for index, row in enumerate(rows):
        row_identifier = f"row_{index}"
        user_id = str(row.get('user_id')) if row.get('user_id') not in (None, '') else None
        email_raw = (row.get('email') or '').strip()
        email = email_raw.lower()
        level = (row.get('level') or '').strip()
        department = (row.get('department') or '').strip()
        password_value = row.get('password') if isinstance(row.get('password'), str) else ''
        password_changed = bool(row.get('password_changed'))
        marked_for_deletion = bool(row.get('marked_for_deletion'))
        is_new = bool(row.get('is_new')) or user_id is None

        if user_id:
            if user_id in seen_ids:
                _error('duplicate_user_id')
            seen_ids.add(user_id)
            if user_id not in existing_users:
                _error('unknown_user_id')
        if not email:
            _error('email_required')
        else:
            try:
                email_validator(email)
            except ValidationError:
                _error('email_invalid')
        if level not in level_labels.values():
            _error('level_required')

        if level == level_labels[AdminUser.LEVEL_DEPARTMENT]:
            if not department:
                _error('department_required')
            elif department not in allowed_departments:
                _error('department_invalid')
        elif department and department not in allowed_departments:
            _error('department_invalid')

        if password_changed and not password_value:
            _error('password_required')

        if not marked_for_deletion:
            if email in planned_email_map and planned_email_map[email] != user_id:
                _error('email_not_unique')
            planned_email_map[email] = user_id or row_identifier

        validated_rows.append(
            {
                'user_id': user_id,
                'email': email,
                'level': level,
                'department': department,
                'password': password_value,
                'password_changed': password_changed,
                'marked_for_deletion': marked_for_deletion,
                'is_new': is_new,
            }
        )

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    # Uniqueness against database excluding rows marked for deletion
    allowed_ids = {row['user_id'] for row in validated_rows if row['user_id']}
    final_emails = [row['email'] for row in validated_rows if not row['marked_for_deletion']]
    for candidate in set(final_emails):
        qs = AdminUser.objects.filter(email__iexact=candidate)
        if allowed_ids:
            qs = qs.exclude(id__in=allowed_ids)
        if qs.exists():
            _error('email_not_unique')
            break

    # Prevent removing/downgrading last admin
    final_admins = 0
    for row in validated_rows:
        if row['marked_for_deletion']:
            continue
        if row['level'] == level_labels[AdminUser.LEVEL_ADMIN]:
            final_admins += 1

    if final_admins == 0:
        _error('no_admin_left')

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    updated_users: list[AdminUser] = []
    tokens_to_send: list[tuple[AdminUser, str]] = []
    with transaction.atomic():
        for row in validated_rows:
            if row['marked_for_deletion'] and row['user_id']:
                user = existing_users.get(row['user_id'])
                if user and user.level == AdminUser.LEVEL_ADMIN and final_admins < 1:
                    continue
                if user:
                    user.delete()
                continue

            if row['user_id']:
                user = existing_users[row['user_id']]
                email_changed = user.email.lower() != row['email']
                level_changed = user.level != row['level']
                department_changed = user.department != row['department']
                password_regenerated = False
                password_changed = row.get('password_changed', False)
                user.email = row['email']
                user.level = row['level']
                user.department = row['department']
                if password_changed:
                    user.set_password_token(row.get('password', ''))
                    tokens_to_send.append((user, row.get('password', '')))
                elif email_changed:
                    token = user.regenerate_token_hash()
                    tokens_to_send.append((user, token))
                    password_regenerated = True
                elif not user.password_hash:
                    token = user.regenerate_token_hash()
                    tokens_to_send.append((user, token))
                    password_regenerated = True
                if email_changed or level_changed or department_changed or password_changed or password_regenerated:
                    user.save()
                else:
                    user.save(update_fields=['updated_at'])
            else:
                user = AdminUser(email=row['email'], level=row['level'], department=row['department'])
                if row.get('password_changed'):
                    password_value = row.get('password', '')
                    user.set_password_token(password_value)
                    token = password_value
                else:
                    token = user.regenerate_token_hash()
                user.save()
                tokens_to_send.append((user, token))
            updated_users.append(user)

    if tokens_to_send:
        transaction.on_commit(
            lambda: [
                send_admin_user_credentials(email=user.email, token=token, user=user)
                for user, token in tokens_to_send
            ]
        )

    response_users = [_serialise_admin_user(user) for user in AdminUser.objects.all().order_by('id')]
    return JsonResponse({'users': response_users})


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
        log_action(
            AdminActivityLog.ACTION_EMAIL,
            description=f"Manual email sent to {form.cleaned_data['to_email']}",
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
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorized'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    if not _can_access_message(admin_user, message):
        return JsonResponse({'error': 'forbidden'}, status=403)
    language = get_language(request)
    return JsonResponse(_serialise_admin_message(message, language))


@require_POST
def update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if admin_user.level == AdminUser.LEVEL_TESTER:
        return JsonResponse({'error': 'forbidden'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    if not _can_access_message(admin_user, message):
        return JsonResponse({'error': 'forbidden'}, status=403)
    language = get_language(request)
    form = MessageUpdateForm(request.POST, instance=message)
    if form.is_valid():
        updated_message = form.save()
        return JsonResponse(_serialise_admin_message(updated_message, language))

    return JsonResponse({'errors': form.errors}, status=400)


@require_POST
def rollback_client_change(request: HttpRequest, message_id: int, log_id: int) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    if admin_user.level == AdminUser.LEVEL_TESTER:
        return JsonResponse({'error': 'forbidden'}, status=403)

    message = get_object_or_404(ContactMessage, pk=message_id, is_deleted=False)
    if not _can_access_message(admin_user, message):
        return JsonResponse({'error': 'forbidden'}, status=403)
    with transaction.atomic():
        log_entry = get_object_or_404(
            ClientChangeLog.objects.select_for_update(),
            pk=log_id,
            message=message,
            is_reverted=False,
        )

        field_name = log_entry.field
        setattr(message, field_name, log_entry.previous_value)
        message.save(update_fields=[field_name])

        log_entry.is_reverted = True
        log_entry.save(update_fields=['is_reverted'])

    log_action(
        AdminActivityLog.ACTION_ROLLBACK,
        message_id=message.id,
        description=f"Rolled back field {field_name}",
    )

    language = get_language(request)
    return JsonResponse(_serialise_admin_message(message, language))
