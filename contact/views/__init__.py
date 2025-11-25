"""
# === FILE SUMMARY ===
# Purpose: Expose public interface for contact view functions.
# Responsible for: Importing view callables and defining __all__ for easier imports.
# Connected to: Individual view modules (public, auth, portal, admin, user).
# Important classes/functions: __all__ export list
# Notes: Simplifies module imports across the project.
# =====================================
"""

from .auth import login, logout
from .portal import panel
from .public import index
from .admin import (
    admin_panel,
    admin_profile,
    admin_reset_password,
    admin_settings,
    admin_verify_password,
    message_detail,
    rollback_client_change,
    update_message,
)
from .user import (
    access_portal,
    restore_access,
    user_delete_message,
    user_message_detail,
    user_requests,
    user_update_message,
)

__all__ = [
    'index',
    'login',
    'logout',
    'panel',
    'admin_panel',
    'admin_settings',
    'admin_reset_password',
    'admin_profile',
    'admin_verify_password',
    'access_portal',
    'restore_access',
    'message_detail',
    'update_message',
    'rollback_client_change',
    'user_requests',
    'user_message_detail',
    'user_update_message',
    'user_delete_message',
]
