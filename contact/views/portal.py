# === FILE SUMMARY ===
# Purpose: Route the main portal endpoint to either the admin or user-facing experience.
# Responsible for: Checking session login state and delegating to appropriate view handlers.
# Connected to: admin_panel view for authenticated admins, access_portal view for user access flow.
# Important classes/functions: panel()
# Notes: Restricts accepted HTTP methods to GET and POST.
# =====================================
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
