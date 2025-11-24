# === FILE SUMMARY ===
# Purpose: Add department field to AdminUser.
# Responsible for: Extending adminuser table with optional department reference field.
# Connected to: AdminUser model evolution.
# Important classes/functions: Migration
# Notes: Uses simple CharField for department linkage.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contact", "0008_adminuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="adminuser",
            name="department",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
