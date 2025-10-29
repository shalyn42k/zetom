from __future__ import annotations

import hashlib

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
