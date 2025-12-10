"""
# === FILE SUMMARY ===
# Purpose: Admin-facing views for managing contact messages, attachments, admin users, and associated actions.
# Responsible for: Rendering the admin panel, handling bulk actions, trash management, downloads, email sending, and admin user CRUD via JSON API.
# Connected to: Forms for filtering/actions, ContactMessage and related models, helper utilities, email/pdf services, session state.
# Important classes/functions: admin_panel(), admin_settings(), _handle_* helpers, _serialise_admin_message(), _get_admin_user()
# Notes: Enforces access control via session data and department-level permissions; relies on supporting services for persistence.
# =====================================
"""

from __future__ import annotations

import json
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import EmailValidator
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST, require_http_methods

from ..forms import (
    DownloadMessagesForm,
    EmailForm,
    MessageBulkActionForm,
    MessageFilterForm,
    MessageUpdateForm,
    TrashActionForm,
)
from ..models import (
    AdminActivityLog,
    AdminUser,
    ClientChangeLog,
    ContactMessage,
    Department,
    build_permissions_override,
    default_permissions_for_level,
    resolve_permission_profile,
    _generate_access_token,
)
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
    user_id = request.session.get('admin_user_id')
    if not user_id:
        return None
    try:
        return AdminUser.objects.prefetch_related('departments').get(id=user_id)
    except AdminUser.DoesNotExist:
        return None


def _permission_profile(admin_user: AdminUser | None) -> dict[str, object]:
    if not admin_user:
        return {"mode": "inherit", "permissions": default_permissions_for_level(AdminUser.LEVEL_TESTER)}
    return resolve_permission_profile(admin_user.level_of_access, admin_user.permissions_override)


def _can_access_message(admin_user: AdminUser | None, message: ContactMessage) -> bool:
    if not admin_user:
        return False
    if admin_user.level_of_access == AdminUser.LEVEL_DEPARTMENT:
        departments = {dept.code for dept in admin_user.departments.all()}
        if not departments:
            return False
        return message.company in departments
    return True


def _apply_company_filter(
    queryset,
    *,
    company_filter: str | None,
    allowed_companies: set[str] | None,
    user_level: str,
    valid_companies: set[str],
):
    if user_level == AdminUser.LEVEL_DEPARTMENT and allowed_companies:
        queryset = queryset.filter(company__in=allowed_companies)

    if company_filter and company_filter != MessageFilterForm.COMPANY_ALL:
        if user_level == AdminUser.LEVEL_DEPARTMENT:
            if allowed_companies and company_filter in allowed_companies:
                queryset = queryset.filter(company=company_filter)
        elif company_filter in valid_companies:
            queryset = queryset.filter(company=company_filter)

    return queryset


@require_http_methods(["GET", "POST"])
@login_required(login_url='/login/')
def admin_panel(request: HttpRequest) -> HttpResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return redirect('contact:login')

    user_level = admin_user.level_of_access
    permission_profile = _permission_profile(admin_user)
    permissions = permission_profile.get("permissions", {})
    can_edit_messages = bool(permissions.get("can_edit_messages"))
    can_delete_messages = bool(permissions.get("can_delete_messages"))
    can_export_messages = bool(permissions.get("can_export_messages"))
    can_send_emails = bool(permissions.get("can_send_emails"))
    user_departments = list(admin_user.departments.values_list('code', flat=True))
    allowed_companies: set[str] | None = (
        set(user_departments) if user_level == AdminUser.LEVEL_DEPARTMENT else None
    )
    readonly_mode = not can_edit_messages
    lang = get_language(request)

    # --- company / department options ---
    company_options = helpers.company_options(lang)  # [{'value': 'Elektrotechniczne', 'label': 'Elektrotechniczne'}, ...]
    department_labels = helpers.company_labels(lang)
    department_choices = [
        (code, department_labels.get(code, code)) for code in user_departments
    ]

    # --- read filters ---
    if user_level == AdminUser.LEVEL_DEPARTMENT:
        filter_data = helpers.resolve_filter_data(
            request,
            lang,
            company_choices=department_choices,
            include_all=len(department_choices) > 1,
        )
    else:
        filter_data = helpers.resolve_filter_data(request, lang)

    sort_by: str | None = filter_data["sort_by"]
    company_filter: str | None = filter_data["company"]

    # valid companies for level1/3 dropdown protection
    valid_companies: set[str] = (
        allowed_companies
        if allowed_companies is not None
        else {item["value"] for item in company_options}
    )

    # --- base querysets ---
    if user_level == AdminUser.LEVEL_DEPARTMENT and not user_departments:
        queryset = ContactMessage.objects.none()
        deleted_queryset = ContactMessage.objects.none()
    else:
        queryset = _apply_company_filter(
            message_service.get_messages(sort_by=sort_by),
            company_filter=company_filter,
            allowed_companies=allowed_companies,
            user_level=user_level,
            valid_companies=valid_companies,
        )
        deleted_queryset = _apply_company_filter(
            message_service.get_deleted_messages(),
            company_filter=company_filter,
            allowed_companies=allowed_companies,
            user_level=user_level,
            valid_companies=valid_companies,
        )

    # --- pagination ---
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page') or request.POST.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # --- form choices ---
    choices = [(str(message.id), f"#{message.id}") for message in page_obj.object_list]
    deleted_choices = [
        (str(message.id), f"#{message.id} · {message.email}")
        for message in deleted_queryset
    ]

    action_form = MessageBulkActionForm(request.POST or None, message_choices=choices)
    helpers.localise_action_choices(action_form, lang)

    email_form = EmailForm(request.POST or None, request.FILES or None)
    trash_form = TrashActionForm(
        request.POST or None,
        message_choices=deleted_choices,
        language=lang,
    )

    download_choices_raw = list(queryset.values_list("id", "email"))
    download_choices = [
        (str(message_id), f"#{message_id} · {email}")
        for message_id, email in download_choices_raw
    ]
    download_form = DownloadMessagesForm(
        request.POST or None,
        message_choices=download_choices,
        language=lang,
    )

    # --- readonly mode ---
    if not (can_edit_messages or can_delete_messages):
        action_form.fields["action"].disabled = True
        action_form.fields["selected"].disabled = True
    if not can_send_emails:
        for field in email_form.fields.values():
            field.disabled = True
    if not can_delete_messages:
        for field in trash_form.fields.values():
            field.disabled = True
    if not can_export_messages:
        for field in download_form.fields.values():
            field.disabled = True

    # --- filter form object (UI) ---
    filter_form = helpers.build_filter_form(
        request,
        lang,
        initial_data=filter_data,
        company_choices=(
            department_choices if user_level == AdminUser.LEVEL_DEPARTMENT else None
        ),
        include_all=(
            user_level != AdminUser.LEVEL_DEPARTMENT
            or len(department_choices) > 1
        ),
    )

    if user_level == AdminUser.LEVEL_DEPARTMENT:
        filter_form.fields["company"].initial = filter_data.get("company")
        filter_form.fields["company"].widget.attrs["disabled"] = False

    # --- POST handlers ---
    if request.method == "POST":
        form_name = (request.POST.get("form_name") or "").strip()
        if form_name == "bulk":
            if not (can_edit_messages or can_delete_messages):
                messages.error(
                    request,
                    "Brak uprawnień do wykonania akcji." if lang == "pl" else "You do not have permission to perform this action.",
                    extra_tags="admin",
                )
                return redirect(
                    helpers.panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
            action_form, response = _handle_bulk_form(
                request,
                lang,
                choices,
                page_obj,
                sort_by,
                company_filter,
                allowed_companies,
                can_edit_messages,
                can_delete_messages,
            )
            if response:
                return response
        elif form_name == "trash":
            if not can_delete_messages:
                messages.error(
                    request,
                    "Brak uprawnień do opróżniania kosza." if lang == "pl" else "You cannot modify trash.",
                    extra_tags="admin",
                )
                return redirect(
                    helpers.panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
            trash_form, response = _handle_trash_form(
                request,
                lang,
                deleted_choices,
                page_obj,
                sort_by,
                company_filter,
                allowed_companies,
                can_delete_messages,
            )
            if response:
                return response
        elif form_name == "download":
            if not can_export_messages:
                messages.error(
                    request,
                    "Brak uprawnień do eksportu." if lang == "pl" else "You cannot export messages.",
                    extra_tags="admin",
                )
                return redirect(
                    helpers.panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
            download_form, response = _handle_download_form(
                request,
                lang,
                download_choices,
                sort_by,
                company_filter,
                allowed_companies,
                user_level,
                valid_companies,
                can_export_messages,
            )
            if response:
                return response
        else:
            if not can_send_emails:
                messages.error(
                    request,
                    "Brak uprawnień do wysyłania wiadomości." if lang == "pl" else "You cannot send emails from this panel.",
                    extra_tags="admin",
                )
                return redirect(
                    helpers.panel_redirect_url(
                        lang,
                        page_obj.number,
                        sort_by=sort_by,
                        company=company_filter,
                    )
                )
            email_form, response = _handle_email_form(
                request,
                lang,
                page_obj,
                sort_by,
                company_filter,
                can_send_emails,
            )
            if response:
                return response

    # --- extra context for templates / JS ---
    download_fields_total = len(download_form.fields["fields"].choices)
    selected_download_ids: list[str] = []
    if download_form.is_bound:
        raw_ids = download_form.data.getlist("messages")
        selected_download_ids = list(dict.fromkeys(raw_ids))

    # >>> ВАЖНО: здесь ГАРАНТИРОВАННО готовый JSON <<<
    status_options = helpers.status_options(lang)
    status_meta = {
        item["value"]: {"label": item["label"], "badge": item["badge"]}
        for item in status_options
    }

    status_meta_json = json.dumps(status_meta)

    permission_defaults = {
        level: default_permissions_for_level(level) for level, _ in AdminUser.LEVEL_CHOICES
    }
    permission_defaults_json = json.dumps(permission_defaults)
    permission_profile_json = json.dumps(permission_profile)

    if lang == "pl":
        detail_error_message = "Nie udało się pobrać danych zgłoszenia."
        update_error_message = (
            "Nie udało się zapisać zmian. Popraw błędy i spróbuj ponownie."
        )
    else:
        detail_error_message = "Unable to load request data."
        update_error_message = (
            "Could not save changes. Please fix the errors and try again."
        )

    user_department_labels = [department_labels.get(code, code) for code in user_departments]

    context = {
        "lang": lang,
        "user_level": user_level,
        "user_departments": user_departments,
        "user_department_labels": user_department_labels,
        "admin_user_email": admin_user.email,
        "admin_user_id": admin_user.id,
        "readonly_mode": readonly_mode,
        "messages_page": page_obj,
        "paginator": paginator,
        "page_range": list(
            paginator.get_elided_page_range(
                page_obj.number, on_each_side=1, on_ends=1
            )
        ),
        "deleted_messages": deleted_queryset,
        "action_form": action_form,
        "email_form": email_form,
        "trash_form": trash_form,
        "download_form": download_form,
        "filter_form": filter_form,
        "current_page": page_obj.number,
        "current_sort": sort_by,
        "current_company": company_filter,
        "download_has_choices": bool(download_choices),
        "download_fields_total": download_fields_total,
        "selected_download_ids": selected_download_ids,
        "company_options": company_options,
        "status_options": status_options,
        "status_meta_json": status_meta_json,
        "permission_defaults_json": permission_defaults_json,
        "permission_profile_json": permission_profile_json,
        "request_detail_error_message": detail_error_message,
        "request_update_error_message": update_error_message,
        "can_edit_messages": can_edit_messages,
        "can_delete_messages": can_delete_messages,
        "can_export_messages": can_export_messages,
        "can_send_emails": can_send_emails,
    }
    return render(request, "contact/admin_panel.html", context)


def _serialise_admin_user(user: AdminUser) -> dict:
    permission_profile = resolve_permission_profile(
        user.level_of_access, user.permissions_override
    )
    return {
        'user_id': user.id,
        'email': user.email,
        'password_plaintext': '',
        'has_password': bool(user.password_hash),
        'level': user.level_of_access,
        'departments': list(user.departments.values_list('code', flat=True)),
        'permissions': permission_profile.get('permissions', {}),
        'permissions_mode': permission_profile.get('mode', 'inherit'),
        'role_permissions': default_permissions_for_level(user.level_of_access),
    }


def _queue_credentials_emails(pairs: list[tuple[AdminUser, str]]) -> None:
    if not pairs:
        return

    transaction.on_commit(
        lambda: [
            send_admin_user_credentials(email=user.email, token=token, user=user)
            for user, token in pairs
        ]
    )


@require_http_methods(["GET", "POST"])
@login_required(login_url='/login/')
def admin_settings(request: HttpRequest) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorised'}, status=403)

    if admin_user.level_of_access != AdminUser.LEVEL_ADMIN:
        return JsonResponse({'error': 'forbidden'}, status=403)

    language = get_language(request)
    allowed_departments = set(Department.objects.values_list('code', flat=True))
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
        'cannot_delete_self': 'Nie możesz usunąć własnego konta administratora.'
        if language == 'pl'
        else 'You cannot delete your own admin account.',
    }

    email_validator = EmailValidator(message=error_messages['email_invalid'])

    if request.method == 'GET':
        users = [
            _serialise_admin_user(user)
            for user in AdminUser.objects.prefetch_related('departments').all().order_by('id')
        ]
        return JsonResponse({'users': users})

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        return JsonResponse({'errors': [error_messages['invalid_payload']]}, status=400)

    rows = payload.get('users', []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return JsonResponse({'errors': [error_messages['invalid_payload']]}, status=400)

    existing_users = {
        str(user.id): user
        for user in AdminUser.objects.prefetch_related('departments').all()
    }
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
        departments_raw = row.get('departments')
        departments_list = departments_raw if isinstance(departments_raw, list) else []
        departments = [str(value).strip() for value in departments_list if str(value).strip()]
        password_value = row.get('password') if isinstance(row.get('password'), str) else ''
        password_changed = bool(row.get('password_changed')) if level == AdminUser.LEVEL_ADMIN else False
        marked_for_deletion = bool(row.get('marked_for_deletion'))
        is_new = bool(row.get('is_new')) or user_id is None
        permissions_raw = row.get('permissions') if isinstance(row.get('permissions'), dict) else {}
        permissions_mode = row.get('permissions_mode')
        permissions_override = build_permissions_override(
            level,
            {'mode': permissions_mode, 'permissions': permissions_raw},
        )

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
        if level not in {choice[0] for choice in AdminUser.LEVEL_CHOICES}:
            _error('level_required')

        if level == AdminUser.LEVEL_DEPARTMENT:
            if not departments:
                _error('department_required')
            else:
                invalid_departments = [dept for dept in departments if dept not in allowed_departments]
                if invalid_departments:
                    _error('department_invalid')
        elif departments:
            invalid_departments = [dept for dept in departments if dept not in allowed_departments]
            if invalid_departments:
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
                'departments': departments,
                'password': password_value,
                'password_changed': password_changed,
                'marked_for_deletion': marked_for_deletion,
                'is_new': is_new,
                'permissions_override': permissions_override,
            }
        )

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    # Prevent deleting the currently authenticated admin user
    is_self_deletion_planned = any(
        row['marked_for_deletion'] and row['user_id'] == str(admin_user.id)
        for row in validated_rows
    )
    if is_self_deletion_planned:
        return JsonResponse(
            {
                'success': False,
                'errors': {'__all__': [error_messages['cannot_delete_self']]},
            },
            status=400,
        )

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
    final_admins = sum(
        1
        for row in validated_rows
        if not row['marked_for_deletion'] and row['level'] == AdminUser.LEVEL_ADMIN
    )

    if final_admins == 0:
        _error('no_admin_left')

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    departments_lookup = {
        dept.code: dept for dept in Department.objects.filter(code__in=allowed_departments)
    }
    updated_users: list[AdminUser] = []
    def _apply_credentials(user: AdminUser, *, manual_password: str | None, email: str) -> None:
        if manual_password:
            plain_text_password = manual_password
            transaction.on_commit(
                lambda: send_admin_user_credentials(
                    email=email,
                    token=plain_text_password,
                    user=user,
                )
            )
            user.set_password(plain_text_password)
            return

        generated_token = _generate_access_token()
        transaction.on_commit(
            lambda: send_admin_user_credentials(
                email=email,
                token=generated_token,
                user=user,
            )
        )
        user.set_password(generated_token)

    with transaction.atomic():
        for row in validated_rows:
            selected_departments = [departments_lookup[code] for code in row['departments'] if code in departments_lookup]
            if row['marked_for_deletion'] and row['user_id']:
                user = existing_users.get(row['user_id'])
                if user and user.level_of_access == AdminUser.LEVEL_ADMIN and final_admins < 1:
                    continue
                if user:
                    user.delete()
                continue

            if row['user_id']:
                user = existing_users[row['user_id']]
                user.email = row['email']
                user.level_of_access = row['level']
                user.permissions_override = row['permissions_override']

                existing_departments = set(user.departments.values_list('code', flat=True))
                departments_changed = existing_departments != set(row['departments'])
                manual_password = (
                    row.get('password')
                    if row.get('password_changed') and row.get('password')
                    else None
                )
                _apply_credentials(user, manual_password=manual_password, email=row['email'])

                user.save()
                if departments_changed or user.level_of_access == AdminUser.LEVEL_DEPARTMENT:
                    user.departments.set(selected_departments)
            else:
                user = AdminUser(email=row['email'], level_of_access=row['level'])
                password_value = row.get('password') if row.get('password_changed') else ''
                manual_password = password_value or None
                _apply_credentials(user, manual_password=manual_password, email=row['email'])
                user.permissions_override = row['permissions_override']
                user.save()
                if selected_departments:
                    user.departments.set(selected_departments)

            updated_users.append(user)

    response_users = [
        _serialise_admin_user(user)
        for user in AdminUser.objects.prefetch_related('departments').all().order_by('id')
    ]
    return JsonResponse({'users': response_users})


@require_POST
@login_required(login_url='/login/')
def admin_reset_password(request: HttpRequest) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorised'}, status=403)

    if admin_user.level_of_access != AdminUser.LEVEL_ADMIN:
        return JsonResponse({'error': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        payload = request.POST

    user_id = payload.get('user_id') if hasattr(payload, 'get') else None
    if not user_id:
        return JsonResponse({'error': 'user_id_required'}, status=400)

    try:
        target = AdminUser.objects.get(id=user_id)
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    now = timezone.now()
    if target.last_password_reset_at and now - target.last_password_reset_at < timedelta(days=1):
        return JsonResponse(
            {
                'error': 'too_frequent',
                'message': 'Password was already reset in the last 24 hours.',
            },
            status=400,
        )

    new_password = get_random_string(length=10)
    with transaction.atomic():
        target.set_password(new_password)
        target.last_password_reset_at = now
        target.save(update_fields=['password_hash', 'last_password_reset_at'])

    _queue_credentials_emails([(target, new_password)])

    return JsonResponse({'success': True})


@require_http_methods(["POST"])
@login_required(login_url='/login/')
def admin_profile(request: HttpRequest) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'success': False, 'errors': ['unauthorised']}, status=403)

    language = get_language(request)
    messages = {
        'invalid_payload': 'Nieprawidłowy format danych.' if language == 'pl' else 'Invalid payload.',
        'email_required': 'Email jest wymagany.' if language == 'pl' else 'Email is required.',
        'email_invalid': 'Email jest nieprawidłowy.' if language == 'pl' else 'Invalid email format.',
        'email_not_unique': 'Email musi być unikalny.' if language == 'pl' else 'Email must be unique.',
        'old_password_required': 'Podaj aktualne hasło.' if language == 'pl' else 'Current password is required.',
        'old_password_incorrect': 'Nieprawidłowe aktualne hasło.' if language == 'pl' else 'Current password is incorrect.',
        'password_mismatch': 'Hasła nie są takie same.' if language == 'pl' else 'New passwords do not match.',
    }

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        return JsonResponse({'success': False, 'errors': [messages['invalid_payload']]}, status=400)

    email_raw = (payload.get('email') or '').strip()
    email = email_raw.lower()
    old_password = (payload.get('old_password') or '').strip()
    new_password = (payload.get('new_password') or '').strip()
    new_password_confirm = (payload.get('new_password_confirm') or '').strip()

    errors: list[str] = []
    email_validator = EmailValidator(message=messages['email_invalid'])
    if not email:
        errors.append(messages['email_required'])
    else:
        try:
            email_validator(email)
        except ValidationError:
            errors.append(messages['email_invalid'])
        else:
            duplicate_qs = AdminUser.objects.filter(email__iexact=email).exclude(id=admin_user.id)
            if duplicate_qs.exists():
                errors.append(messages['email_not_unique'])

    wants_password_change = bool(new_password or new_password_confirm)
    if wants_password_change:
        if not old_password:
            errors.append(messages['old_password_required'])
        elif not admin_user.check_password(old_password):
            errors.append(messages['old_password_incorrect'])
        if new_password != new_password_confirm:
            errors.append(messages['password_mismatch'])

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    admin_user.email = email
    if wants_password_change and new_password:
        admin_user.set_password(new_password)
    admin_user.save(update_fields=['email', 'password_hash', 'updated_at'])
    request.session['admin_email'] = admin_user.email

    if wants_password_change and new_password:
        _queue_credentials_emails([(admin_user, new_password)])

    return JsonResponse({'success': True, 'email': admin_user.email})


@require_http_methods(["POST"])
@login_required(login_url='/login/')
def admin_verify_password(request: HttpRequest) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'valid': False, 'error': 'unauthorised'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError, AttributeError):
        return JsonResponse({'valid': False, 'error': 'Invalid payload.'}, status=400)

    password = (payload.get('password') or '').strip()
    if not password:
        return JsonResponse({'valid': False, 'error': 'Password is required.'}, status=400)

    if admin_user.check_password(password):
        return JsonResponse({'valid': True})

    return JsonResponse({'valid': False, 'error': 'Incorrect password.'})


def _handle_bulk_form(
    request: HttpRequest,
    lang: str,
    choices: list[tuple[str, str]],
    page_obj,
    sort_by: str | None,
    company_filter: str | None,
    allowed_companies: set[str] | None,
    can_edit_messages: bool,
    can_delete_messages: bool,
):
    submitted_ids = request.POST.getlist('selected') if request.method == 'POST' else []
    existing_values = {value for value, _ in choices}
    extra_choices = [
        (value, f"#{value}") for value in submitted_ids if value not in existing_values
    ]
    merged_choices = [*choices, *extra_choices]

    form = MessageBulkActionForm(request.POST, message_choices=merged_choices)
    helpers.localise_action_choices(form, lang)
    if form.is_valid():
        action = form.cleaned_data['action']
        if action == MessageBulkActionForm.ACTION_DELETE and not can_delete_messages:
            form.add_error(
                None,
                "Brak uprawnień do usuwania." if lang == "pl" else "You cannot delete messages.",
            )
            return form, None
        if action != MessageBulkActionForm.ACTION_DELETE and not can_edit_messages:
            form.add_error(
                None,
                "Brak uprawnień do edycji." if lang == "pl" else "You cannot edit messages.",
            )
            return form, None
        ids = [int(pk) for pk in form.cleaned_data['selected']]
        helpers.handle_action(
            action, ids, lang, request, allowed_companies
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


def _handle_trash_form(
    request: HttpRequest,
    lang: str,
    deleted_choices: list[tuple[str, str]],
    page_obj,
    sort_by: str | None,
    company_filter: str | None,
    allowed_companies: set[str] | None,
    can_delete_messages: bool,
):
    submitted_ids = request.POST.getlist('selected') if request.method == 'POST' else []
    existing_values = {value for value, _ in deleted_choices}
    extra_choices = [
        (value, f"#{value}") for value in submitted_ids if value not in existing_values
    ]
    merged_choices = [*deleted_choices, *extra_choices]

    form = TrashActionForm(request.POST, message_choices=merged_choices, language=lang)
    if form.is_valid():
        if not can_delete_messages:
            form.add_error(
                None,
                "Brak uprawnień do zarządzania koszem." if lang == "pl" else "You cannot manage trash.",
            )
            return form, None
        ids = [int(pk) for pk in form.cleaned_data['selected']]
        helpers.handle_trash_action(
            form.cleaned_data['action'], ids, lang, request, allowed_companies
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


def _handle_download_form(
    request: HttpRequest,
    lang: str,
    download_choices: list[tuple[str, str]],
    sort_by: str | None,
    company_filter: str | None,
    allowed_companies: set[str] | None,
    user_level: str,
    valid_companies: set[str],
    can_export_messages: bool,
):
    form = DownloadMessagesForm(
        request.POST,
        message_choices=download_choices,
        language=lang,
    )
    if not can_export_messages:
        form.add_error(
            None,
            "Brak uprawnień do eksportu." if lang == "pl" else "Export is not allowed.",
        )
        return form, None
    if form.is_valid():
        ids = [int(pk) for pk in form.cleaned_data['messages']]
        fields = form.cleaned_data['fields']
        selected_messages = _apply_company_filter(
            message_service.get_messages(sort_by=sort_by),
            company_filter=company_filter,
            allowed_companies=allowed_companies,
            user_level=user_level,
            valid_companies=valid_companies,
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
    can_send_emails: bool,
):
    form = EmailForm(request.POST, request.FILES or None)
    if not can_send_emails:
        form.add_error(
            None,
            "Brak uprawnień do wysyłania wiadomości." if lang == "pl" else "Email sending is disabled for this account.",
        )
        return form, None
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


@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
@require_POST
def update_message(request: HttpRequest, message_id: int) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    permissions = _permission_profile(admin_user).get("permissions", {})
    if not permissions.get("can_edit_messages"):
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


@login_required(login_url='/login/')
@require_POST
def rollback_client_change(request: HttpRequest, message_id: int, log_id: int) -> JsonResponse:
    admin_user = _get_admin_user(request)
    if not request.session.get('logged_in') or not admin_user:
        return JsonResponse({'error': 'unauthorized'}, status=403)
    permissions = _permission_profile(admin_user).get("permissions", {})
    if not permissions.get("can_edit_messages"):
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
