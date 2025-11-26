"""Department helpers and constants."""

from __future__ import annotations

ALLOWED_DEPARTMENTS: set[str] = {
    "Elektrotechniczne",
    "Dlugosci i Kąta",
    "Mechaniczna",
}

FALLBACK_DEPARTMENT = "inne"


def normalize_department_code(raw_value: str | None) -> str:
    """Return a normalised department code with a fallback.

    Empty or unknown values are converted to ``FALLBACK_DEPARTMENT``.
    """

    value = (raw_value or "").strip()
    if value not in ALLOWED_DEPARTMENTS:
        return FALLBACK_DEPARTMENT
    return value


DEFAULT_DEPARTMENTS: list[tuple[str, str, str]] = [
    ("Elektrotechniczne", "Elektrotechniczne", "Electrotechnical"),
    ("Dlugosci i Kąta", "Dlugosci i Kąta", "Length and Angle"),
    ("Mechaniczna", "Mechaniczna", "Mechanical"),
    (FALLBACK_DEPARTMENT, "Inne", "Other"),
]
