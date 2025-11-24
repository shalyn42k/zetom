# === FILE SUMMARY ===
# Purpose: WSGI entrypoint for deploying the zetom project with synchronous servers.
# Responsible for: Setting the settings module, initialising the WSGI app, and wrapping it with WhiteNoise for static/media files.
# Connected to: zetom_project.settings, WhiteNoise configuration, deployment servers.
# Important classes/functions: get_wsgi_application(), WhiteNoise
# Notes: Adds media files dynamically when MEDIA_URL and MEDIA_ROOT are set.
# =====================================
import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zetom_project.settings')

application = get_wsgi_application()
application = WhiteNoise(application)

media_prefix = settings.MEDIA_URL.lstrip('/') if settings.MEDIA_URL else ''
if media_prefix and settings.MEDIA_ROOT:
    application.add_files(str(settings.MEDIA_ROOT), prefix=media_prefix)
