# === FILE SUMMARY ===
# Purpose: Persist activity logs for admin actions on contact messages.
# Responsible for: Recording single and bulk actions with optional descriptions within database transactions.
# Connected to: AdminActivityLog model, Django transaction management, admin view helpers.
# Important classes/functions: log_bulk_action(), log_action()
# Notes: Bulk logging uses bulk_create with conflict ignoring to avoid duplication issues.
# =====================================
from __future__ import annotations

from typing import Iterable

from django.db import transaction

from ..models import AdminActivityLog


@transaction.atomic
def log_bulk_action(action: str, message_ids: Iterable[int], *, description: str | None = None) -> None:
    """Persist a log entry for each affected message."""

    ids = [int(mid) for mid in message_ids if mid is not None]
    if not ids:
        return
    entries = [
        AdminActivityLog(
            message_id=mid,
            action=action,
            description=description or "",
        )
        for mid in ids
    ]
    AdminActivityLog.objects.bulk_create(entries, ignore_conflicts=True)


def log_action(action: str, *, message_id: int | None = None, description: str | None = None) -> None:
    AdminActivityLog.objects.create(
        message_id=message_id,
        action=action,
        description=description or "",
    )
