# Purpose: Add department FK to ContactMessage and backfill from company codes.
# Connected to: ContactMessage and Department models for department-level access control.
from __future__ import annotations

from django.db import migrations, models


def backfill_departments(apps, schema_editor) -> None:
    ContactMessage = apps.get_model("contact", "ContactMessage")
    Department = apps.get_model("contact", "Department")

    for department in Department.objects.all():
        ContactMessage.objects.filter(
            department__isnull=True,
            company=department.code,
        ).update(department=department)


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0015_adminuser_permissions_override"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                to="contact.department",
            ),
        ),
        migrations.RunPython(backfill_departments, migrations.RunPython.noop),
    ]
