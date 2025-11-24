# === FILE SUMMARY ===
# Purpose: Migration replacing is_read boolean with a status field on ContactMessage.
# Responsible for: Altering the schema to include status choices and removing obsolete is_read field.
# Connected to: ContactMessage model updates reflecting status tracking.
# Important classes/functions: Migration
# Notes: Introduces default status value 'new' and indexes.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "new"),
                    ("in_progress", "in_progress"),
                    ("ready", "ready"),
                ],
                db_index=True,
                default="new",
                max_length=32,
            ),
        ),
        migrations.RunSQL(
            sql="UPDATE contact_contactmessage SET status = CASE WHEN is_read THEN 'ready' ELSE 'new' END",
            reverse_sql="UPDATE contact_contactmessage SET status = CASE WHEN status = 'ready' THEN 'ready' ELSE 'new' END",
        ),
        migrations.RemoveField(
            model_name="contactmessage",
            name="is_read",
        ),
    ]
