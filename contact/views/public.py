from __future__ import annotations

import logging
import math
import smtplib

from django.conf import settings
from django.contrib import messages
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
from ..utils import get_language
from . import helpers

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def index(request: HttpRequest) -> HttpResponse:
    lang = get_language(request)
    form = ContactForm(request.POST or None, request.FILES or None, language=lang)
    success_message = request.session.pop('contact_success', None)

    throttle_seconds = getattr(settings, 'CONTACT_FORM_THROTTLE_SECONDS', 30)
    form_valid = False
    throttle_error = False
    submission_timestamp: float | None = None

    if request.method == 'POST':
        form_valid = form.is_valid()
        submission_timestamp = timezone.now().timestamp()
        last_submission_raw = request.session.get('contact_last_submission')
        try:
            last_submission_ts = float(last_submission_raw)
        except (TypeError, ValueError):
            last_submission_ts = None

        if last_submission_ts is not None and submission_timestamp is not None:
            elapsed = submission_timestamp - last_submission_ts
            if elapsed < throttle_seconds:
                remaining_seconds = max(1, int(math.ceil(throttle_seconds - elapsed)))
                if lang == 'pl':
                    error_message = f'Proszę poczekać {remaining_seconds} s przed ponownym wysłaniem formularza.'
                else:
                    error_message = f'Please wait {remaining_seconds} s before submitting the form again.'
                form.add_error(None, error_message)
                throttle_error = True

    if request.method == 'POST' and form_valid and not throttle_error:
        payload = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"],
            "phone": form.cleaned_data["phone"],
            "email": form.cleaned_data["email"],
            "company": form.cleaned_data["company"],
            "message": form.cleaned_data["message"],
        }
        attachments = form.cleaned_data.get("attachments") or []
        try:
            message, access_token = message_service.add_message(
                **payload,
                attachments=attachments,
            )
        except Exception:  # pragma: no cover - guarded by DB transaction
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
                helpers.remember_user_message(request, message.id)
                if submission_timestamp is not None:
                    request.session['contact_last_submission'] = submission_timestamp
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
    }
    return render(request, 'contact/index.html', context)
