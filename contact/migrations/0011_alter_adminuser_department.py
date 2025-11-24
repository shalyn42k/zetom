# === FILE SUMMARY ===
# Purpose: Adjust AdminUser department to many-to-many relationship.
# Responsible for: Removing single department field and adding M2M to Department model.
# Connected to: AdminUser and Department relational changes.
# Important classes/functions: Migration
# Notes: Uses intermediate table creation for many-to-many mapping.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contact", "0010_adminuser_password_ciphertext"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adminuser",
            name="department",
            field=models.CharField(
                blank=True,
                choices=[
                    ("firma1", "Company 1"),
                    ("firma2", "Company 2"),
                    ("firma3", "Company 3"),
                    ("inna", "Other"),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
