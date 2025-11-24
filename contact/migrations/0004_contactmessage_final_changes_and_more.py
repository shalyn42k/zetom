
# === FILE SUMMARY ===
# Purpose: Extend ContactMessage with final_changes and final_response fields and adjust status.
# Responsible for: Adding text fields for admin responses and modifying status default behaviour.
# Connected to: ContactMessage model updates used in admin workflows.
# Important classes/functions: Migration
# Notes: Supports capturing final resolution details.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0003_contactmessage_is_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="final_changes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="final_response",
            field=models.TextField(blank=True),
        ),
    ]
