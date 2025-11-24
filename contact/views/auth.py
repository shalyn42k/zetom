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

from django.core.cache import cache   # ← добавили

from ..models import AdminUser
from ..forms import LoginForm
from ..utils import get_language

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = LoginForm(request.POST or None)
    ip = request.META.get('REMOTE_ADDR', 'unknown')

    back_url = request.GET.get('next') or f"{reverse('contact:index')}?lang={lang}"

    # Инициализируем переменные, чтобы они всегда существовали
    blocked = False
    time_left = None

    # === НОВАЯ ЗАЩИТА ОТ BRUTE-FORCE НА CACHE ===
    cache_key_attempts = f"login_attempts:{ip}"
    cache_key_block = f"login_block_until:{ip}"

    blocked_until = cache.get(cache_key_block)

    if blocked_until and timezone.now() < blocked_until:
        blocked = True
        remaining = int((blocked_until - timezone.now()).total_seconds())
        minutes, seconds = divmod(remaining, 60)
        time_left = f"{minutes:02d}:{seconds:02d}"
    else:
        blocked = False
        time_left = None
        # Если блокировка истекла — чистим кэш
        if blocked_until:
            cache.delete(cache_key_attempts)
            cache.delete(cache_key_block)

    if request.method == 'POST' and not blocked and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        try:
            user = AdminUser.objects.get(email__iexact=email)
        except AdminUser.DoesNotExist:
            user = None
        except (OperationalError, ProgrammingError) as exc:
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
            # УСПЕШНЫЙ ЛОГИН — чистим счётчики
            cache.delete(cache_key_attempts)
            cache.delete(cache_key_block)

            # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ — РЕГЕНЕРАЦИЯ SESSION ID
            request.session.flush()  # Убиваем старую сессию полностью
            request.session['logged_in'] = True
            request.session['admin_user_id'] = user.id
            request.session['level_of_access'] = user.level_of_access
            request.session['departments'] = list(
                user.departments.values_list('code', flat=True)
            )
            request.session['admin_email'] = user.email
            request.session['lang'] = lang

            # Сохраняем новую сессию
            request.session.save()

            panel_url = reverse('contact:panel')
            if lang:
                panel_url = f"{panel_url}?lang={lang}"
            return redirect(panel_url)
        # НЕУДАЧНАЯ ПОПЫТКА
        attempts = cache.get(cache_key_attempts, 0) + 1
        cache.set(cache_key_attempts, attempts, timeout=600)  # 10 минут храним счётчик

        if attempts >= 5:
            block_until = timezone.now() + timedelta(minutes=5)
            cache.set(cache_key_block, block_until, timeout=300)
            blocked = True
            time_left = "05:00"
        else:
            attempts_left = 5 - attempts
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

    # ← Этот return всегда будет работать, потому что blocked и time_left уже определены
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