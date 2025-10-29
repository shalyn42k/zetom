import json
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_COOKIE_AGE = max(1800, int(os.getenv('SESSION_COOKIE_AGE', '3600')))
SESSION_SAVE_EVERY_REQUEST = False  # Не обновлять expiration на каждый запрос.
SESSION_COOKIE_SECURE = True  # Только HTTPS.
SESSION_COOKIE_HTTPONLY = True  # Защита от JS-доступа.
SESSION_COOKIE_SAMESITE = 'Strict'  # Защита от CSRF в cross-site.

# --- Core ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-insecure-key-change-me')
DJANGO_DEBUG = os.getenv("DJANGO_DEBUG", "true").strip().lower()
DEBUG = DJANGO_DEBUG in ("1", "true", "yes", "on")

# Hosts / CSRF
allowed_hosts_env = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip() and not h.strip().startswith("${")
]

# Render автоматически задаёт домен в переменной RENDER_EXTERNAL_HOSTNAME.
# Добавим его в списки хостов/происхождений, чтобы избежать ошибок 400.
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()

ALLOWED_HOSTS = allowed_hosts_env
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))

# Для Django 4+ лучше указывать со схемой: https://example.com
csrf_trusted = [
    o.strip()
    for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip() and not o.strip().startswith("${")
]
if render_hostname:
    csrf_origin = f"https://{render_hostname}"
    if csrf_origin not in csrf_trusted:
        csrf_trusted.append(csrf_origin)

CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_trusted))

# --- Cache ---
default_cache_backend = os.getenv(
    'DJANGO_CACHE_BACKEND', 'django.core.cache.backends.filebased.FileBasedCache'
)
default_cache_location = os.getenv('DJANGO_CACHE_LOCATION', str(BASE_DIR / 'cache'))

CACHES = {
    'default': {
        'BACKEND': default_cache_backend,
        'LOCATION': default_cache_location,
    }
}

if default_cache_backend.endswith('FileBasedCache'):
    os.makedirs(default_cache_location, exist_ok=True)


# --- Apps ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'contact',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise добавим ниже условно в проде
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'zetom_project.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'zetom_project.wsgi.application'

# --- DB ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('SQLITE_NAME', BASE_DIR / 'db.sqlite3'),
    }
}

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    conn_max_age = int(os.getenv('DB_CONN_MAX_AGE', '600'))
    default_ssl = 'false' if DEBUG else 'true'
    ssl_require = os.getenv('DB_SSL_REQUIRE', default_ssl).lower() in ('1', 'true', 'yes', 'on')
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=conn_max_age,
        ssl_require=ssl_require,
    )

# --- Auth ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- I18N ---
LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

# --- Static / Media ---
STATIC_URL = '/static/'

media_root_env = os.getenv('MEDIA_ROOT')
MEDIA_ROOT = Path(media_root_env) if media_root_env else BASE_DIR / 'media'
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')

default_file_storage = os.getenv(
    'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage'
)

STORAGES = {
    'default': {
        'BACKEND': default_file_storage,
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

if default_file_storage == 'django.core.files.storage.FileSystemStorage':
    STORAGES['default']['OPTIONS'] = {'location': str(MEDIA_ROOT)}

DEFAULT_FILE_STORAGE = STORAGES['default']['BACKEND']

if DEBUG:
    # DEV: источники статики, без STATIC_ROOT!
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    # PROD: сборка в STATIC_ROOT + WhiteNoise
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    # если есть BASE_DIR/static — можно добавить как источник
    STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

    # Подключаем WhiteNoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES['staticfiles'] = {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }

# --- Security (prod) ---
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() in ("1", "true", "yes", "on")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False

# --- Email ---
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "").strip() or (
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() in ('1', 'true', 'yes', 'on')
EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASS', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@example.com')

# Совместимость со старым кодом (чтобы settings.SMTP_* существовали)
SMTP_SERVER = EMAIL_HOST
SMTP_PORT = EMAIL_PORT
SMTP_USER = EMAIL_HOST_USER
SMTP_PASS = EMAIL_HOST_PASSWORD

def _load_company_notification_recipients() -> dict[str, list[str]]:
    raw_value = os.getenv('COMPANY_NOTIFICATION_RECIPIENTS', '').strip()
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ImproperlyConfigured(
            'COMPANY_NOTIFICATION_RECIPIENTS must contain valid JSON data.'
        ) from exc
    if not isinstance(parsed, dict):
        raise ImproperlyConfigured('COMPANY_NOTIFICATION_RECIPIENTS must be a JSON object.')

    recipients: dict[str, list[str]] = {}
    for key, value in parsed.items():
        if isinstance(value, str):
            emails = [item.strip() for item in value.split(',') if item and item.strip()]
        elif isinstance(value, (list, tuple, set)):
            emails = [str(item).strip() for item in value if str(item).strip()]
        else:
            raise ImproperlyConfigured(
                'COMPANY_NOTIFICATION_RECIPIENTS values must be lists or comma separated strings.'
            )
        recipients[str(key).strip()] = emails
    return recipients


COMPANY_NOTIFICATION_RECIPIENTS = _load_company_notification_recipients()

# Ссылка, которая будет добавляться в письма-уведомления для сотрудников фирм
COMPANY_NOTIFICATION_LINK = os.environ.get(
    "COMPANY_NOTIFICATION_LINK",
    "http://localhost:8000/contact/panel/",
)

# --- Other ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'pl')
LOGIN_URL = 'contact:login'

CONTACT_FORM_THROTTLE_SECONDS = int(os.getenv('CONTACT_FORM_THROTTLE_SECONDS', '30'))
CONTACT_FORM_RATE_LIMIT_PREFIX = os.getenv('CONTACT_FORM_RATE_LIMIT_PREFIX', 'contact_form')
CONTACT_ACCESS_TOKEN_TTL_HOURS = int(os.getenv('CONTACT_ACCESS_TOKEN_TTL_HOURS', '72'))
SMTP_RETRY_ATTEMPTS = int(os.getenv('SMTP_RETRY_ATTEMPTS', '2'))
SMTP_TIMEOUT = int(os.getenv('SMTP_TIMEOUT', '30'))
ATTACH_MAX_SIZE_MB = int(os.getenv('ATTACH_MAX_SIZE_MB', '25'))
ATTACH_ALLOWED_TYPES = os.getenv(
    'ATTACH_ALLOWED_TYPES',
    'application/pdf,image/jpeg,image/png,text/plain',
).split(',')
ATTACH_ALLOWED_EXTENSIONS = [
    ext.strip().lower()
    for ext in os.getenv('ATTACH_ALLOWED_EXTENSIONS', '.pdf,.png,.jpg,.jpeg,.txt').split(',')
    if ext.strip()
]
ATTACH_SCAN_COMMAND = os.getenv('ATTACH_SCAN_COMMAND', '').strip()

SENTRY_DSN = os.getenv('SENTRY_DSN', '').strip()
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.0'))

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImproperlyConfigured('sentry-sdk must be installed to enable Sentry monitoring.') from exc

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
    )


def _validate_environment_configuration() -> None:
    if DEBUG:
        return

    required_vars = {
        'DJANGO_SECRET_KEY': SECRET_KEY,
        'SMTP_SERVER': EMAIL_HOST,
        'SMTP_USER': EMAIL_HOST_USER,
        'SMTP_PASS': EMAIL_HOST_PASSWORD,
    }
    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        raise ImproperlyConfigured(
            f"Missing required environment configuration: {', '.join(sorted(missing))}"
        )
    if SECRET_KEY == 'dev-insecure-key-change-me':
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set in production.')
    if not COMPANY_NOTIFICATION_RECIPIENTS:
        raise ImproperlyConfigured('COMPANY_NOTIFICATION_RECIPIENTS must be configured in production.')


_validate_environment_configuration()
