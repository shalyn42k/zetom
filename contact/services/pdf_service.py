from __future__ import annotations

from io import BytesIO
from typing import Iterable

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from xml.sax.saxutils import escape # or from html import escape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models import ContactMessage


def build_messages_pdf(
    messages: Iterable[ContactMessage],
    *,
    fields: list[str],
    language: str,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=24 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"].clone("Title")
    title_style.textColor = colors.HexColor("#1b6d34")
    title_style.fontSize = 18
    title_style.spaceAfter = 12

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#5b6c6c"),
        fontSize=10,
        spaceAfter=18,
    )

    field_label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceAfter=4,
    )

    field_value_style = ParagraphStyle(
        "FieldValue",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )

    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor("#2fa84f"),
    )

    story: list = []
    generated_at = timezone.localtime()
    if language == "pl":
        title = "Zgłoszenia kontaktowe"
        subtitle = f"Wygenerowano: {generated_at.strftime('%Y-%m-%d %H:%M')}"
    else:
        title = "Contact requests"
        subtitle = f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M')}"

    story.append(Paragraph(escape(title), title_style))
    story.append(Paragraph(escape(subtitle), subtitle_style))

    status_labels = _status_labels(language)
    field_labels = _field_labels(language)

    messages = list(messages)
    if not messages:
        empty_text = "Brak danych do wyświetlenia." if language == "pl" else "No requests to display."
        story.append(Paragraph(escape(empty_text), styles["Normal"]))
        doc.build(story)
        return buffer.getvalue()

    for index, message in enumerate(messages, start=1):
        section_title = (
            f"Zgłoszenie #{message.id}" if language == "pl" else f"Request #{message.id}"
        )
        story.append(Paragraph(escape(section_title), section_title_style))

        rows = []
        for field in fields:
            label = field_labels.get(field, field)
            value = _field_value(field, message, status_labels, language)
            rows.append([
                Paragraph(f"<b>{escape(label)}</b>", field_label_style),
                Paragraph(value, field_value_style),
            ])

        table = Table(rows, colWidths=[45 * mm, 120 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.HexColor("#dce7de")),
                ]
            )
        )
        story.append(table)

        if index < len(messages):
            story.append(Spacer(1, 18))

    doc.build(story)
    return buffer.getvalue()


def _field_labels(language: str) -> dict[str, str]:
    if language == "pl":
        return {
            "created_at": "Data zgłoszenia",
            "customer": "Klient",
            "phone": "Telefon",
            "email": "E-mail",
            "company": "Firma",
            "message": "Wiadomość",
            "status": "Status",
        }
    return {
        "created_at": "Submitted at",
        "customer": "Customer",
        "phone": "Phone",
        "email": "Email",
        "company": "Company",
        "message": "Message",
        "status": "Status",
    }


def _status_labels(language: str) -> dict[str, str]:
    if language == "pl":
        return {
            ContactMessage.STATUS_NEW: "Nowe",
            ContactMessage.STATUS_IN_PROGRESS: "W trakcie",
            ContactMessage.STATUS_READY: "Gotowe",
        }
    return {
        ContactMessage.STATUS_NEW: "New",
        ContactMessage.STATUS_IN_PROGRESS: "In progress",
        ContactMessage.STATUS_READY: "Ready",
    }


def _field_value(
    field: str,
    message: ContactMessage,
    status_labels: dict[str, str],
    language: str,
) -> str:
    if field == "created_at":
        timestamp = timezone.localtime(message.created_at)
        fmt = "%Y-%m-%d %H:%M"
        return escape(timestamp.strftime(fmt))
    if field == "customer":
        full_name = f"{message.first_name} {message.last_name}".strip()
        return escape(full_name)
    if field == "phone":
        return escape(message.phone)
    if field == "email":
        return escape(message.email)
    if field == "company":
        return escape(message.company)
    if field == "message":
        text = message.message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [escape(line) for line in text.split("\n")]
        return "<br/>".join(lines)
    if field == "status":
        return escape(status_labels.get(message.status, message.status))
    return ""
