import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_COOKIE_AGE = 60  # Сессия живет max 1 мин, даже если не del.
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
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# Получатели нотификаций по компаниям. Заполните реальные почты на месте примеров.
COMPANY_NOTIFICATION_RECIPIENTS = {
    # Для фирмы 1 отправка сотруднику, менеджеру и дополнительному контакту
    "firma1": [
        "tymirdanylov1@gmail.com",
        "ilitovko660@gmail.com",
        "volkovnikita1977@gmail.com",
    ],
    # Для фирмы 2
    "firma2": [
        "tymirdanylov1@gmail.com",
        "ilitovko660@gmail.com",
        "volkovnikita1977@gmail.com",
    ],
    # Для фирмы 3
    "firma3": [
        "tymirdanylov1@gmail.com",
        "ilitovko660@gmail.com",
        "volkovnikita1977@gmail.com",
    ],
    # Общий список по умолчанию для всех остальных компаний (например, "inna")
    "default": [
        "tymirdanylov1@gmail.com",
        "ilitovko660@gmail.com",
        "volkovnikita1977@gmail.com",
    ],
}

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
