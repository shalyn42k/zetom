from __future__ import annotations

import base64
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def get_language(request) -> str:
    lang = request.GET.get('lang')
    if lang:
        request.session['lang'] = lang
        return lang
    session_lang = request.session.get('lang')
    if session_lang:
        return session_lang
    return settings.DEFAULT_LANGUAGE


def get_client_ip(request) -> str:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        for ip in forwarded_for.split(','):
            candidate = ip.strip()
            if candidate:
                return candidate
    return (request.META.get('REMOTE_ADDR') or '').strip()


def build_rate_limit_key(prefix: str, identifier: str) -> str:
    identifier = identifier or 'anonymous'
    digest = hashlib.sha256(identifier.encode('utf-8')).hexdigest()
    return f"{prefix}:{digest}"


def _admin_password_key() -> bytes:
    secret = getattr(settings, 'ADMIN_PASSWORD_SECRET', None) or settings.SECRET_KEY
    digest = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)


def _admin_password_cipher() -> Fernet:
    return Fernet(_admin_password_key())


def encrypt_admin_secret(value: str) -> str:
    if not value:
        return ''
    cipher = _admin_password_cipher()
    token = cipher.encrypt(value.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_admin_secret(token: str | bytes) -> str | None:
    if not token:
        return None
    cipher = _admin_password_cipher()
    try:
        decrypted = cipher.decrypt(token if isinstance(token, bytes) else token.encode('utf-8'))
    except InvalidToken:
        return None
    return decrypted.decode('utf-8')
