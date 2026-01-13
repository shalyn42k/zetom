# === FILE SUMMARY ===
# Purpose: Handle the public contact form, throttling, persistence, notifications, and contextual data for the landing page.
# Responsible for: Validating submissions, enforcing rate limits, saving messages, sending emails, and preparing view context.
# Connected to: ContactForm, message_service, email_service, Django cache and settings.
# Important classes/functions: index()
# Notes: Respects attachment and throttling settings while providing multi-language messaging.
# =====================================
from __future__ import annotations

import json
import logging
import math
import smtplib
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ..forms import ContactForm
from ..services import messages as message_service
from ..services.email_service import (
    send_company_notification,
    send_contact_email,
)
from ..utils import build_rate_limit_key, get_client_ip, get_language

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None, request.FILES or None, language=lang)
    success_message = request.session.pop('contact_success', None)

    throttle_seconds = getattr(settings, 'CONTACT_FORM_THROTTLE_SECONDS', 30)
    throttle_prefix = getattr(settings, 'CONTACT_FORM_RATE_LIMIT_PREFIX', 'contact_form')
    form_valid = False
    throttle_error = False
    submission_timestamp: float | None = None
    cache_keys: list[str] = []

    if request.method == 'POST':
        captcha_token = (request.POST.get("g-recaptcha-response") or "").strip()
        print("reCAPTCHA token:", captcha_token)
        captcha_response_data: dict[str, object] = {}
        captcha_valid = False
        if settings.RECAPTCHA_SECRET_KEY and captcha_token:
            payload = urllib.parse.urlencode(
                {
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": captcha_token,
                    "remoteip": get_client_ip(request) or "",
                }
            ).encode()
            try:
                with urllib.request.urlopen(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data=payload,
                    timeout=10,
                ) as response:
                    captcha_response_data = json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                logger.exception("Failed to verify reCAPTCHA")
                captcha_response_data = {"success": False, "error": str(exc)}
        else:
            error_reason = (
                "missing-secret-key"
                if not settings.RECAPTCHA_SECRET_KEY
                else "missing-input"
            )
            captcha_response_data = {"success": False, "error": error_reason}
        print("reCAPTCHA response JSON:", captcha_response_data)
        captcha_valid = bool(captcha_response_data.get("success"))
        print("reCAPTCHA valid:", captcha_valid)

        submission_timestamp = timezone.now().timestamp()
        client_identifier = get_client_ip(request) or request.session.session_key or 'anonymous'
        ip_key = build_rate_limit_key(f'{throttle_prefix}:ip', client_identifier)
        cache_keys.append(ip_key)

        raw_email = (request.POST.get('email') or '').strip().lower()
        email_key = build_rate_limit_key(f'{throttle_prefix}:email', raw_email) if raw_email else None
        if email_key:
            cache_keys.append(email_key)

        remaining_durations: list[float] = []
        for key in cache_keys:
            last_submission_raw = cache.get(key)
            if last_submission_raw is None:
                continue
            try:
                last_submission_ts = float(last_submission_raw)
            except (TypeError, ValueError):
                continue
            elapsed = submission_timestamp - last_submission_ts
            if elapsed < throttle_seconds:
                remaining_durations.append(throttle_seconds - elapsed)

        if remaining_durations:
            remaining_seconds = max(1, int(math.ceil(max(remaining_durations))))
            if lang == 'pl':
                error_message = f'Proszę poczekać {remaining_seconds} s przed ponownym wysłaniem formularza.'
            else:
                error_message = f'Please wait {remaining_seconds} s before submitting the form again.'
            form.add_error(None, error_message)
            throttle_error = True

        form_valid = form.is_valid()
        if not captcha_valid:
            captcha_message = (
                "Potwierdź, że nie jesteś botem."
                if lang == "pl"
                else "Please confirm you are not a bot."
            )
            form.add_error("bot_check", captcha_message)
        form_valid = form_valid and captcha_valid

    if request.method == 'POST' and form_valid and not throttle_error:
        payload = {
            "full_name": form.cleaned_data["full_name"],
            "phone": form.cleaned_data["phone"],
            "email": form.cleaned_data["email"],
            "company": form.cleaned_data["company"],
            "company_name": form.cleaned_data["company_name"],
            "message": form.cleaned_data["message"],
        }
        attachments = form.cleaned_data.get("attachments") or []
        try:
            message, access_token = message_service.add_message(
                **payload,
                attachments=attachments,
            )
        except DatabaseError:
            logger.exception('Failed to persist contact message')
            if lang == 'pl':
                error_text = 'Nie udało się zapisać zgłoszenia. Spróbuj ponownie później.'
            else:
                error_text = 'Unable to save the request right now. Please try again later.'
            form.add_error(None, error_text)
        else:
            try:
                if settings.SMTP_USER:
                    send_contact_email(
                        form.cleaned_data['email'],
                        message,
                        access_token=access_token,
                    )
                    notification_link = request.build_absolute_uri(reverse('contact:panel'))
                    send_company_notification(message, link=notification_link)
            except smtplib.SMTPException:
                logger.exception('Failed to send contact form emails')
                message.delete()
                if lang == 'pl':
                    error_text = 'Nie udało się wysłać wiadomości e-mail. Spróbuj ponownie później.'
                else:
                    error_text = 'Unable to send the email right now. Please try again later.'
                form.add_error(None, error_text)
            else:
                if submission_timestamp is not None:
                    for key in cache_keys:
                        cache.set(key, submission_timestamp, throttle_seconds)
                if lang == 'pl':
                    success_message = (
                        'Wiadomość została wysłana. Zostanie przetworzona w ciągu 48 godzin, po czym się z Tobą skontaktujemy. '
                        f'Numer zgłoszenia: #{message.id}. Token dostępu wysłano na e-mail.'
                    )
                else:
                    success_message = (
                        'Your request has been sent. We will process it within 48 hours and contact you afterwards. '
                        f'Request number: #{message.id}. The access token was sent to your e-mail.'
                    )
                messages.success(request, success_message)
                request.session['contact_success'] = success_message
                return redirect(f"{reverse('contact:index')}?lang={lang}")

    allowed_types = [
        content_type.strip()
        for content_type in getattr(settings, 'ATTACH_ALLOWED_TYPES', [])
        if content_type.strip()
    ]

    context = {
        'form': form,
        'lang': lang,
        'success_message': success_message,
        'throttle_seconds': throttle_seconds,
        'max_attachment_size': getattr(settings, 'ATTACH_MAX_SIZE_MB', 25),
        'allowed_attachment_types': allowed_types,
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    }
    return render(request, 'contact/index.html', context)
