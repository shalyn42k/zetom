from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from ..forms import LoginForm
from ..models import AdminUser
from ..utils import get_language

logger = logging.getLogger(__name__)

failed_attempts: dict[str, int] = {}
blocked_ips: dict[str, timezone.datetime] = {}


@require_http_methods(["GET", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    has_admin_accounts = AdminUser.objects.exists()
    form = LoginForm(request.POST or None, require_email=has_admin_accounts)
    ip = request.META.get('REMOTE_ADDR', 'unknown')

    blocked = False
    time_left = None

    if ip in blocked_ips:
        if timezone.now() < blocked_ips[ip]:
            blocked = True
            remaining_time = blocked_ips[ip] - timezone.now()
            total_seconds = int(remaining_time.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            time_left = f"{minutes:02d}:{seconds:02d}"
        else:
            blocked_ips.pop(ip, None)
            failed_attempts[ip] = 0

    if request.method == 'POST' and not blocked and form.is_valid():
        password = form.cleaned_data['password']
        email = (form.cleaned_data.get('email') or '').strip()
        if has_admin_accounts:
            user = AdminUser.objects.filter(email__iexact=email).first()
            if user and check_password(password, user.token_hash):
                _persist_session(request, user)
                failed_attempts[ip] = 0
                return redirect('contact:panel')
            error_message = (
                'Nieprawidłowy e-mail lub token.'
                if lang == 'pl'
                else 'Incorrect e-mail or token.'
            )
            form.add_error(None, error_message)
        elif password == settings.ADMIN_PASSWORD:
            request.session['logged_in'] = True
            request.session['user_level'] = AdminUser.LEVEL_1
            request.session['user_department'] = 'all'
            request.session['user_email'] = 'admin@local'
            failed_attempts[ip] = 0
            return redirect('contact:panel')
        else:
            form.add_error(
                'password',
                'Nieprawidłowe hasło.' if lang == 'pl' else 'Wrong password.',
            )
        failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
        if failed_attempts[ip] >= 5:
            blocked_ips[ip] = timezone.now() + timedelta(minutes=5)
            blocked = True
            remaining_time = blocked_ips[ip] - timezone.now()
            total_seconds = int(remaining_time.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            time_left = f"{minutes:02d}:{seconds:02d}"
        else:
            attempts_left = 5 - failed_attempts[ip]
            if has_admin_accounts:
                error_message = (
                    'Nieprawidłowy e-mail lub token. Pozostało prób: {attempts_left}'
                    if lang == 'pl'
                    else 'Incorrect e-mail or token. Attempts left: {attempts_left}'
                )
                form.add_error(None, error_message.format(attempts_left=attempts_left))
            else:
                error_message = (
                    f"Nieprawidłowe hasło! Pozostało prób: {attempts_left}"
                    if lang == 'pl'
                    else f"Wrong password! Attempts left: {attempts_left}"
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
            'has_admin_accounts': has_admin_accounts,
            'back_url': f"{reverse('contact:index')}?lang={lang}",
        },
    )


def _persist_session(request: HttpRequest, user: AdminUser) -> None:
    request.session['logged_in'] = True
    request.session['user_level'] = user.level
    request.session['user_department'] = user.department or 'all'
    request.session['user_email'] = user.email
    request.session['admin_user_id'] = user.id


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    request.session.flush()
    return redirect(f"{reverse('contact:index')}?lang={lang}")
