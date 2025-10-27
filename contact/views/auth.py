from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from ..forms import LoginForm
from ..utils import get_language

logger = logging.getLogger(__name__)

failed_attempts: dict[str, int] = {}
blocked_ips: dict[str, timezone.datetime] = {}


@require_http_methods(["GET", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = LoginForm(request.POST or None)
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
        if form.cleaned_data['password'] == settings.ADMIN_PASSWORD:
            request.session['logged_in'] = True
            failed_attempts[ip] = 0
            return redirect('contact:panel')
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
        },
    )


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    request.session.flush()
    return redirect(f"{reverse('contact:index')}?lang={lang}")
