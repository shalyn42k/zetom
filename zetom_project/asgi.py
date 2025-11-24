# === FILE SUMMARY ===
# Purpose: ASGI entrypoint for deploying the zetom project with asynchronous servers.
# Responsible for: Initialising Django settings and exposing the ASGI application callable.
# Connected to: zetom_project.settings for configuration, ASGI server infrastructure.
# Important classes/functions: get_asgi_application(), application
# Notes: Ensures default settings module is set before creating the ASGI application.
# =====================================
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zetom_project.settings')

application = get_asgi_application()
