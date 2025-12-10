"""
Role-based permission defaults for admin users.
"""

ROLE_PERMISSIONS: dict[str, dict[str, bool]] = {
    'level1': {
        'edit_requests': True,
        'export_pdf': True,
        'send_manual_email': True,
        'manage_users': True,
        'use_trash': True,
    },
    'level2': {
        'edit_requests': True,
        'export_pdf': True,
        'send_manual_email': True,
        'manage_users': False,
        'use_trash': True,
    },
    'level3': {
        'edit_requests': False,
        'export_pdf': False,
        'send_manual_email': False,
        'manage_users': False,
        'use_trash': False,
    },
}
