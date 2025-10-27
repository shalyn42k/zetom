from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from .admin import admin_panel
from .user import access_portal


@require_http_methods(["GET", "POST"])
def panel(request: HttpRequest) -> HttpResponse:
    if request.session.get('logged_in'):
        return admin_panel(request)
    return access_portal(request)
