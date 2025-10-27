from __future__ import annotations

import mimetypes
from typing import Iterable

from django.conf import settings
from django.core.exceptions import ValidationError


def _detect_content_type(upload) -> str:
    content_type = getattr(upload, "content_type", None)
    if content_type:
        return content_type
    guess, _ = mimetypes.guess_type(getattr(upload, "name", ""))
    return guess or "application/octet-stream"


def validate_uploads(files: Iterable, *, allow_empty: bool = True) -> list:
    files = list(files or [])
    if not files and allow_empty:
        return []
    if not files:
        raise ValidationError("No files provided.")

    max_total_mb = getattr(settings, "ATTACH_MAX_SIZE_MB", 25)
    allowed_types = set(getattr(settings, "ATTACH_ALLOWED_TYPES", []))
    max_total_bytes = max_total_mb * 1024 * 1024

    total_size = 0
    cleaned = []

    for upload in files:
        size = getattr(upload, "size", None)
        if size is None:
            raise ValidationError("Unable to determine file size.")
        total_size += size
        if total_size > max_total_bytes:
            raise ValidationError(
                f"Combined attachments exceed the {max_total_mb} MB limit."
            )
        content_type = _detect_content_type(upload)
        if allowed_types and content_type not in allowed_types:
            raise ValidationError(
                f"Files of type {content_type} are not allowed."
            )
        cleaned.append((upload, content_type, size))

    return cleaned

