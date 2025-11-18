from __future__ import annotations

from io import BytesIO
from typing import Iterable
from html import escape  # ← используем стандартный экранировщик

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
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

    summary_label_style = ParagraphStyle(
        "SummaryLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#1b6d34"),
    )

    summary_value_style = ParagraphStyle(
        "SummaryValue",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#234c39"),
    )

    field_label_style = ParagraphStyle(
        "FieldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#1b6d34"),
    )

    field_value_style = ParagraphStyle(
        "FieldValue",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )

    section_header_title_style = ParagraphStyle(
        "SectionHeaderTitle",
        parent=styles["Heading2"],
        fontSize=13,
        spaceAfter=0,
        textColor=colors.HexColor("#1b6d34"),
    )

    section_header_meta_style = ParagraphStyle(
        "SectionHeaderMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#5b6c6c"),
        alignment=TA_RIGHT,
    )

    story: list = []
    generated_at = timezone.localtime()
    if language == "pl":
        title = "Zgłoszenia kontaktowe"
        subtitle = f"Wygenerowano: {generated_at.strftime('%Y-%m-%d %H:%M')}"
        summary_requests_label = "Liczba zgłoszeń"
        summary_fields_label = "Uwzględnione pola"
    else:
        title = "Contact requests"
        subtitle = f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M')}"
        summary_requests_label = "Total requests"
        summary_fields_label = "Included fields"

    story.append(Paragraph(escape(title), title_style))
    story.append(Paragraph(escape(subtitle), subtitle_style))

    status_labels = _status_labels(language)
    field_labels = _field_labels(language)

    messages = list(messages)
    selected_field_labels = [field_labels.get(field, field) for field in fields]

    summary_rows = [
        [
            Paragraph(escape(summary_requests_label), summary_label_style),
            Paragraph(str(len(messages)), summary_value_style),
        ],
        [
            Paragraph(escape(summary_fields_label), summary_label_style),
            Paragraph(
                "<br/>".join(
                    f"&#8226; {escape(label)}" for label in selected_field_labels
                )
                or "-",
                summary_value_style,
            ),
        ],
    ]

    summary_table = Table(summary_rows, colWidths=[55 * mm, 120 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f8f4")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce7de")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dce7de")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 18))

    if not messages:
        empty_text = "Brak danych do wyświetlenia." if language == "pl" else "No requests to display."
        story.append(Paragraph(escape(empty_text), styles["Normal"]))
        doc.build(story)
        return buffer.getvalue()

    for index, message in enumerate(messages, start=1):
        section_title = (
            f"Zgłoszenie #{message.id}" if language == "pl" else f"Request #{message.id}"
        )
        timestamp = timezone.localtime(message.created_at)
        meta_parts = [timestamp.strftime("%Y-%m-%d %H:%M")]
        if message.company:
            meta_parts.append(message.company)
        if message.email:
            meta_parts.append(message.email)
        section_meta = " · ".join(part for part in meta_parts if part)

        header_table = Table(
            [
                [
                    Paragraph(escape(section_title), section_header_title_style),
                    Paragraph(escape(section_meta), section_header_meta_style),
                ]
            ],
            colWidths=[110 * mm, 65 * mm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e8f4eb")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7e1ce")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 8))

        rows = []
        for field in fields:
            label = field_labels.get(field, field)
            value = _field_value(field, message, status_labels)
            rows.append([
                Paragraph(f"<b>{escape(label)}</b>", field_label_style),
                Paragraph(value, field_value_style),
            ])

        table = Table(rows, colWidths=[50 * mm, 120 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fbf9")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#dce7de")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e6efe7")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)

        if index < len(messages):
            story.append(Spacer(1, 20))

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
) -> str:
    if field == "created_at":
        timestamp = timezone.localtime(message.created_at)
        fmt = "%Y-%m-%d %H:%M"
        return escape(timestamp.strftime(fmt))
    if field == "customer":
        return escape(message.full_name)
    if field == "phone":
        return escape(message.phone)
    if field == "email":
        return escape(message.email)
    if field == "company":
        return escape(message.company)
    if field == "company_name":
        return escape(message.company_name)
    if field == "message":
        text = message.message.replace("\r\n", "\n").replace("\r", "\n")
        lines = [escape(line) for line in text.split("\n")]
        return "<br/>".join(lines)
    if field == "status":
        return escape(status_labels.get(message.status, message.status))
    return ""
