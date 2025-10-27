from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from ..models import Activity, Request

User = get_user_model()


def log_activity(
    *,
    request_obj: Request,
    activity_type: str,
    message: str = "",
    actor: User | None = None,
    is_public: bool = False,
    meta: dict[str, Any] | None = None,
) -> Activity:
    return Activity.objects.create(
        request=request_obj,
        actor=actor,
        type=activity_type,
        message=message,
        is_public=is_public,
        meta=meta or {},
    )

