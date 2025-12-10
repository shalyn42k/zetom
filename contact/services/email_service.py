"""
# === FILE SUMMARY ===
# Purpose: Email delivery utilities for contact messages, admin credentials, and notifications.
# Responsible for: Building and sending plain emails or PDFs, handling SMTP retries, and routing messages to appropriate recipients.
# Connected to: Django settings for SMTP configuration, ContactMessage and AdminUser models, standard library email utilities.
# Important classes/functions: send_contact_email(), send_admin_user_credentials(), send_company_notification(), send_email_with_attachment(), _smtp_connection()
# Notes: Respects SMTP retry/timeout settings and optional company notification recipients/links.
# =====================================
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from contextlib import contextmanager
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import IO

from django.conf import settings
from django.utils import timezone

from ..models import AdminUser, ContactMessage

logger = logging.getLogger(__name__)


def send_contact_email(recipient: str, message: ContactMessage, *, access_token: str) -> None:
    subject = 'Nowa wiadomość z formularza kontaktowego'
    expires_at = (
        timezone.localtime(message.access_token_expires_at).strftime('%Y-%m-%d %H:%M')
        if message.access_token_expires_at
        else '—'
    )
    body = (
        'Imię i nazwisko: {full_name}\n'
        'Telefon: {phone}\n'
        'E-mail: {email}\n'
        'Firma: {company}\n'
        'Nazwa firmy: {company_name}\n'
        'Numer zgłoszenia: #{id}\n'
        'Token dostępu: {token}\n'
        'Token ważny do: {expires}\n\n'
        'Wiadomość: {content}\n\n'
        'Zachowaj ten token, aby móc ponownie podejrzeć lub edytować zgłoszenie.'
    ).format(
        full_name=message.full_name,
        phone=message.phone,
        email=message.email,
        company=message.company,
        company_name=message.company_name or '—',
        id=message.id,
        token=access_token,
        expires=expires_at,
        content=message.message,
    )
    _send_plain_email(to_email=recipient, subject=subject, body=body)


def send_admin_user_credentials(*, email: str, token: str, user: AdminUser | None = None) -> None:
    subject = "Your ZETOM admin panel access"
    role_label = None
    if user:
        role_label = {
            AdminUser.LEVEL_ADMIN: "level1",
            AdminUser.LEVEL_DEPARTMENT: "level2",
            AdminUser.LEVEL_TESTER: "level3",
        }.get(user.level_of_access)

    body_lines = [
        "Hello,",
        "",
        "You have been granted access to the ZETOM admin panel.",
        f"Email: {email}",
        f"Temporary password/token: {token}",
    ]

    if role_label:
        body_lines.append(f"Role: {role_label}")
    if user:
        departments = [dept.code for dept in user.departments.all()]
        if departments:
            body_lines.append(f"Departments: {', '.join(departments)}")

    body_lines.extend(
        [
            "",
            "Please log in using your email address and this password.",
            "We recommend changing it after your first login, if allowed.",
        ]
    )

    _send_plain_email(to_email=email, subject=subject, body="\n".join(body_lines))


def send_company_notification(message: ContactMessage, *, link: str | None = None) -> None:
    recipients_config = getattr(settings, "COMPANY_NOTIFICATION_RECIPIENTS", {})
    if not recipients_config:
        return

    company_key = (message.company or "").strip()
    recipients = recipients_config.get(company_key) or recipients_config.get("default") or []

    notification_link = link or getattr(settings, "COMPANY_NOTIFICATION_LINK", "")
    subject = "Новая заявка для проверки"
    body = (
        "Заявка пришла, прошу проверить по этой ссылке: {link}\n\n"
        "Базовая информация:\n"
        "ФИО: {full_name}\n"
        "Телефон: {phone}\n"
        "Email: {email}\n"
        "Компания (kod): {company}\n"
        "Название компании: {company_name}\n\n"
        "Сообщение:\n{content}"
    ).format(
        link=notification_link,
        full_name=message.full_name,
        phone=message.phone,
        email=message.email,
        company=message.company,
        company_name=message.company_name or '—',
        content=message.message,
    )

    for email in recipients:
        if email:
            _send_plain_email(to_email=email, subject=subject, body=body)


def send_email_with_attachment(
    *,
    to_email: str,
    subject: str,
    body: str,
    attachment: IO[bytes] | None,
    filename: str | None,
) -> None:
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    if attachment and filename and filename.endswith('.pdf'):
        pdf = MIMEApplication(attachment.read(), _subtype='pdf')
        pdf.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(pdf)

    _send_message(msg)


def _send_plain_email(*, to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = settings.SMTP_USER
    msg['To'] = to_email
    _send_message(msg)


def _send_message(msg) -> None:
    if not settings.SMTP_USER:
        return

    attempts = max(1, getattr(settings, "SMTP_RETRY_ATTEMPTS", 2))
    last_error: smtplib.SMTPException | None = None

    for attempt in range(1, attempts + 1):
        try:
            with _smtp_connection() as server:
                server.send_message(msg)
        except smtplib.SMTPServerDisconnected as exc:
            last_error = exc
            if attempt >= attempts:
                raise
            logger.warning(
                "SMTP connection dropped during login/send (attempt %s/%s). Retrying...",
                attempt,
                attempts,
            )
            continue
        except smtplib.SMTPException as exc:
            last_error = exc
            raise
        else:
            return

    if last_error is not None:
        raise last_error


@contextmanager
def _smtp_connection():

    host = settings.SMTP_SERVER
    port = int(settings.SMTP_PORT)

    timeout = getattr(settings, "SMTP_TIMEOUT", 30)
    use_ssl = getattr(settings, "EMAIL_USE_SSL", False)

    if use_ssl:
        server: smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)

    try:
        server.ehlo()

        if  port == 587:
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()

        if settings.SMTP_USER and settings.SMTP_PASS:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)

        yield server
    finally:
        try:
            server.quit()
        except:
            server.close()
