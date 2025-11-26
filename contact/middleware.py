"""
Session-based authentication middleware.

This middleware mirrors the existing admin session flags into
`request.user.is_authenticated` so Django's `login_required`
can redirect unauthenticated visitors instead of serving
fallback content.
"""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject


class SessionAdminUser:
    """Lightweight user wrapper driven by admin session data."""

    def __init__(self, request):
        self._request = request

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return self.email or "SessionAdminUser"

    @property
    def is_authenticated(self) -> bool:
        return bool(self._request.session.get("logged_in"))

    @property
    def is_anonymous(self) -> bool:  # pragma: no cover - compatibility helper
        return not self.is_authenticated

    @property
    def email(self) -> str:
        return self._request.session.get("admin_email", "")

    @property
    def id(self):  # pragma: no cover - compatibility helper
        return self._request.session.get("admin_user_id")


def _resolve_user(request, original_user):
    if original_user and original_user.is_authenticated:
        return original_user
    if request.session.get("logged_in"):
        return SessionAdminUser(request)
    return original_user or AnonymousUser()


class SessionAuthenticationMiddleware:
    """Expose session-authenticated admin users to Django's auth system."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        original_user = getattr(request, "user", None)
        request.user = SimpleLazyObject(lambda: _resolve_user(request, original_user))
        response = self.get_response(request)
        return response
