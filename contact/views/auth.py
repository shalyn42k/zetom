from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.db import OperationalError, ProgrammingError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from ..models import AdminUser
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

    back_url = request.GET.get('next') or f"{reverse('contact:index')}?lang={lang}"

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
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        try:
            user = AdminUser.objects.get(email__iexact=email)
        except AdminUser.DoesNotExist:
            user = None
        except (OperationalError, ProgrammingError):
            logger.exception("AdminUser table is not ready; migrations are missing")
            error_message = (
                "Baza użytkowników administratora nie jest gotowa. Uruchom migracje bazy danych."
                if lang == "pl"
                else "Admin user table is not ready. Please run database migrations."
            )
            form.add_error(None, error_message)
            return render(
                request,
                "contact/admin_login.html",
                {
                    "form": form,
                    "lang": lang,
                    "blocked": blocked,
                    "time_left": time_left,
                    "back_url": back_url,
                },
                status=503,
            )

        if user and user.check_password(password):
            request.session['logged_in'] = True
            request.session['user_level'] = user.level_of_access
            request.session['user_email'] = user.email
            request.session['user_id'] = user.id
            request.session['user_departments'] = user.departments or []
            request.session['lang'] = lang
            failed_attempts[ip] = 0
            panel_url = reverse('contact:panel')
            if lang:
                panel_url = f"{panel_url}?lang={lang}"
            return redirect(panel_url)

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
                "Nieprawidłowe dane logowania!"
                if lang == 'pl'
                else "Invalid credentials"
            )
            form.add_error(None, error_message)
            form.add_error('password', (
                f"Pozostało prób: {attempts_left}"
                if lang == 'pl'
                else f"Attempts left: {attempts_left}"
            ))
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
            'back_url': back_url,
        },
    )


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    lang = request.session.get('lang', settings.DEFAULT_LANGUAGE)
    request.session.flush()
    return redirect(f"{reverse('contact:index')}?lang={lang}")
