# === FILE SUMMARY ===
# Purpose: Add password_ciphertext field to AdminUser for encrypted storage.
# Responsible for: Extending AdminUser schema with optional ciphertext column and altering level field choices.
# Connected to: AdminUser model updates.
# Important classes/functions: Migration
# Notes: Supports transition to encrypted password/token storage.
# =====================================
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_adminuser_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminuser',
            name='password_ciphertext',
            field=models.TextField(blank=True),
        ),
    ]
