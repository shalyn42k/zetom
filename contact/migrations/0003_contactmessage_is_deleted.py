# === FILE SUMMARY ===
# Purpose: Add soft-delete flag to ContactMessage.
# Responsible for: Introducing is_deleted boolean with index to support trash functionality.
# Connected to: ContactMessage model where soft deletion is used.
# Important classes/functions: Migration
# Notes: Defaults to False for existing records.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0002_replace_is_read_with_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="is_deleted",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
