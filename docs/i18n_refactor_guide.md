# Zetom i18n Refactor Guide (ru/uk/en/pl)

This guide summarizes how to migrate the project to Django's gettext-based internationalization, add Ukrainian support, and automate translations.

## 1) Settings configuration
1. Enable internationalization and set language choices:
   ```python
   # zetom_project/settings.py
   LANGUAGE_CODE = 'ru'

   LANGUAGES = (
       ('ru', 'Russian'),
       ('uk', 'Ukrainian'),
       ('en', 'English'),
       ('pl', 'Polish'),
   )

   TIME_ZONE = 'Europe/Warsaw'
   USE_I18N = True
   USE_L10N = True
   USE_TZ = True

   LOCALE_PATHS = [BASE_DIR / 'locale']
   ```
2. Middleware order (place `LocaleMiddleware` **after** `SessionMiddleware`, before `CommonMiddleware`):
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.locale.LocaleMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'contact.middleware.SessionAuthenticationMiddleware',
       'django.contrib.messages.middleware.MessageMiddleware',
       'django.middleware.clickjacking.XFrameOptionsMiddleware',
   ]
   ```

## 2) Infrastructure updates (Docker & Render)
- **Dockerfile**: install the gettext toolchain so `compilemessages` works in CI/CD images.
  ```dockerfile
  # System packages for psycopg2-binary, gettext, and building wheels
  RUN apt-get update \
      && apt-get install -y --no-install-recommends build-essential libpq-dev gettext \
      && pip install --no-cache-dir --upgrade pip \
      && rm -rf /var/lib/apt/lists/*
  ```
- **Render.com commands**: append message compilation to builds (and keep migrations/static):
  ```yaml
  # render.yaml (snippet)
  buildCommand: >
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python manage.py collectstatic --noinput && \
    python manage.py migrate --noinput && \
    python manage.py compilemessages

  startCommand: gunicorn zetom_project.wsgi:application
  ```
  If you build without the blueprint, set the Web Service Build Command to include `python manage.py compilemessages` right after migrations/static.

## 3) Template & code refactor strategy
- **Templates**: replace hardcoded strings with translation tags.
  ```django
  <!-- Simple translation -->
  <h1>{% trans "Contact form" %}</h1>

  <!-- With variables -->
  {% blocktrans with user_name=request.user.first_name %}
    Hello, {{ user_name }}! Please leave your message below.
  {% endblocktrans %}
  ```
- **Views/Models (Python)**: wrap human-readable strings with `gettext_lazy`.
  ```python
  # views.py / models.py
  from django.utils.translation import gettext_lazy as _

  class ContactMessage(models.Model):
      subject = models.CharField(max_length=255, verbose_name=_("Subject"))
      body = models.TextField(verbose_name=_("Message body"))

  def contact_created_message(user_email: str) -> str:
      return _("Thank you, %(email)s! We received your request.") % {"email": user_email}
  ```
- **URLs/redirects**: keep using `?lang=uk` or `django.middleware.locale.LocaleMiddleware` will pick the cookie/Accept-Language header.

## 4) Automation (auto-translation script)
- Management command (already added): `contact/management/commands/translate_po.py`.
  ```python
  # python manage.py translate_po --languages uk en pl --source ru
  # Fills empty msgstr/msgstr_plural using GoogleTranslator
  ```
  Behavior highlights:
  - Reads locale roots from `settings.LOCALE_PATHS` (or `BASE_DIR/locale`).
  - Skips missing locale folders and obsolete entries.
  - Translates singular and plural strings separately.
- Dependencies (add to `requirements.txt`):
  ```text
  polib
  deep-translator
  ```

## 5) Execution plan
Run these commands after updating templates/code:
```bash
# 1) Install new deps
pip install -r requirements.txt

# 2) Initialize locale catalogs
python manage.py makemessages -l ru -l uk -l en -l pl

# 3) Auto-fill empty msgstr values (defaults: source=settings.LANGUAGE_CODE)
python manage.py translate_po --languages uk en pl --source ru

# 4) Manually review/fix sensitive strings if needed
# (open locale/<lang>/LC_MESSAGES/django.po)

# 5) Compile translations for runtime
python manage.py compilemessages

# 6) Redeploy/rebuild (Docker/Render will now include compiled .mo files)
```
