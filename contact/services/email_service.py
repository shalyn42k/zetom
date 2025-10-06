from __future__ import annotations

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import IO

from django.conf import settings

from ..models import ContactMessage


def send_contact_email(recipient: str, message: ContactMessage) -> None:
    subject = 'Nowa wiadomość z formularza kontaktowego'
    body = (
        'Imię i nazwisko: {first} {last}\n'
        'Telefon: {phone}\n'
        'E-mail: {email}\n'
        'Firma: {company}\n'
        'Wiadomość: {content}'
    ).format(
        first=message.first_name,
        last=message.last_name,
        phone=message.phone,
        email=message.email,
        company=message.company,
        content=message.message,
    )
    _send_plain_email(to_email=recipient, subject=subject, body=body)


def send_email_with_attachment(*, to_email: str, subject: str, body: str, attachment: IO[bytes] | None, filename: str | None) -> None:
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

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASS:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)
