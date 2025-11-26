# === FILE SUMMARY ===
# Purpose: Route the main portal endpoint to either the admin or user-facing experience.
# Responsible for: Checking session login state and delegating to appropriate view handlers.
# Connected to: admin_panel view for authenticated admins, access_portal view for user access flow.
# Important classes/functions: panel()
# Notes: Restricts accepted HTTP methods to GET and POST.
# =====================================
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods

from .admin import admin_panel


@require_http_methods(["GET", "POST"])
@login_required(login_url='/login/')
def panel(request: HttpRequest) -> HttpResponse:
    return admin_panel(request)
