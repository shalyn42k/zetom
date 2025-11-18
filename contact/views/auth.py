from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from ..forms import AdminLoginForm
from ..models import AdminUser  
from ..utils import get_language

logger = logging.getLogger(__name__)

failed_attempts: dict[str, int] = {}
blocked_ips: dict[str, timezone.datetime] = {}


@require_http_methods(["GET", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = AdminLoginForm(request.POST or None, language=lang)
    ip = request.META.get('REMOTE_ADDR', 'unknown')

    blocked = False
    time_left = None

    if ip in blocked_ips:
        if timezone.now() < blocked_ips[ip]:
            blocked = True
            remaining = blocked_ips[ip] - timezone.now()
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            time_left = f"{minutes:02d}:{seconds:02d}"
        else:
            blocked_ips.pop(ip, None)
            failed_attempts[ip] = 0

    if request.method == 'POST' and not blocked and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            admin_user = AdminUser.objects.get(username=username, is_active=True)
        except AdminUser.DoesNotExist:
            admin_user = None

        if admin_user and admin_user.check_password(password):
            request.session['admin_id'] = admin_user.id
            request.session['admin_name'] = admin_user.full_name or admin_user.username
            failed_attempts[ip] = 0
            return redirect('contact:panel')
        else:
            failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
            if failed_attempts[ip] >= 5:
                blocked_ips[ip] = timezone.now() + timedelta(minutes=5)
                blocked = True
                remaining = blocked_ips[ip] - timezone.now()
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                time_left = f"{minutes:02d}:{seconds:02d}"
            else:
                attempts_left = 5 - failed_attempts[ip]
                error = (
                    f"Nieprawidłowy login lub hasło! Pozostało prób: {attempts_left}"
                    if lang == 'pl'
                    else f"Invalid login or password! Attempts left: {attempts_left}"
                )
                form.add_error(None, error)

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
    request.session.flush()
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    return redirect(f"{reverse('contact:index')}?lang={lang}")
