# === FILE SUMMARY ===
# Purpose: Django application configuration for the contact app.
# Responsible for: Declaring app metadata like default auto field and app label.
# Connected to: INSTALLED_APPS in project settings; contact app components.
# Important classes/functions: ContactConfig
# Notes: Uses BigAutoField by default for model primary keys.
# =====================================
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contact'

    def ready(self):
        from .models import ensure_default_departments

        def _seed_departments(**kwargs):
            ensure_default_departments()

        post_migrate.connect(_seed_departments, sender=self)
