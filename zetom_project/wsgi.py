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
