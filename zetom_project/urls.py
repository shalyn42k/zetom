# === FILE SUMMARY ===
# Purpose: Root URL configuration for the zetom Django project.
# Responsible for: Routing admin and contact application URLs and serving media in development.
# Connected to: contact.urls, Django admin site, settings for DEBUG and media paths.
# Important classes/functions: urlpatterns list
# Notes: Extends media serving only when DEBUG is enabled.
# =====================================
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('contact.urls', namespace='contact')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
