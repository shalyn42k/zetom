# === FILE SUMMARY ===
# Purpose: Django application configuration for the contact app.
# Responsible for: Declaring app metadata like default auto field and app label.
# Connected to: INSTALLED_APPS in project settings; contact app components.
# Important classes/functions: ContactConfig
# Notes: Uses BigAutoField by default for model primary keys.
# =====================================
from django.apps import AppConfig


class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contact'
