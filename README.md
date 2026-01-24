<!--
# === FILE SUMMARY ===
# Purpose: Project overview and setup guide for the Zetom Django application.
# Responsible for: Documenting features, requirements, environment configuration, and local development steps.
# Connected to: manage.py commands, environment variables (.env), dependency installation via requirements.txt.
# Important classes/functions: None
# Notes: Provides commands for migrations, static collection, admin user creation, and running tests.
# =====================================
-->
# Zetom Django Project

Zetom — небольшое Django‑приложение с контактной формой, переводами интерфейса и простым кабинетом управления сообщениями.
Авторизация в панели строится на базе таблицы пользователей, поэтому пароль хранится в БД, а не в `.env`.

## Логика и поток данных

1. Посетитель заполняет контактную форму на публичной странице.
2. Сообщение сохраняется в базе и становится доступным в кабинете.
3. При включённом SMTP отправляется письмо‑уведомление.
4. Операторы работают с сообщениями в панели и могут выгружать PDF‑отчёты.

## Ключевые возможности

- контактная форма и список входящих обращений;
- кабинет управления сообщениями (страницы `/login/` и `/panel/`);
- SMTP‑уведомления (опционально);
- PDF‑отчёты;
- мультиязычный интерфейс (`?lang=en` / `?lang=pl`);
- PostgreSQL‑хранилище сообщений.

## Состав проекта

- Django + PostgreSQL как основная БД;
- `.env` для конфигурации окружения;
- `docker-compose.yml` для быстрого запуска локально;
- команды `manage.py` для миграций, администратора и утилит.

## Требования

- Python 3.11+;
- PostgreSQL 14+ (или Docker);
- pip и virtualenv/venv;
- (опционально) SMTP‑учётка.

## Переменные окружения (кратко)

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`;
- `DATABASE_URL`;
- `SMTP_*` для отправки писем;

## Запуск локально (без Docker)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py create_admin_user you@example.com --level level1
python manage.py runserver
```

Приложение доступно на <http://127.0.0.1:8000/>.

## Запуск через Docker Compose

`docker-compose.yml` поднимает PostgreSQL и Django‑сервер. При необходимости синхронизируйте учётки БД между `db` и `web`.

```bash
docker compose up --build
docker exec -it zetom_app python manage.py migrate
docker exec -it zetom_app python manage.py create_admin_user test@gmail.com --level level1
```

Сервис будет доступен на <http://localhost:8888/>.

## Запуск в Docker вручную (без compose)

```bash
cp .env.example .env
docker network create zetom-net
docker run -d --name zetom-db --network zetom-net -e POSTGRES_DB=zetom -e POSTGRES_USER=zetom -e POSTGRES_PASSWORD=zetom postgres:16
docker build -t zetom:local .
docker run --rm --env-file .env --network zetom-net -p 8888:8888 zetom:local
docker exec -it ИМЯ_КОНТЕЙНЕРА python manage.py migrate
docker exec -it ИМЯ_КОНТЕЙНЕРА python manage.py create_admin_user test@gmail.com --level level1
```

## Если видите ошибку `no such table: django_session`

Это означает, что в используемой базе данных ещё не применены стандартные миграции Django для хранилища сессий.
В проекте подключены `django.contrib.sessions` в `INSTALLED_APPS` и `SessionMiddleware` в `MIDDLEWARE`,
а движок сессий использует базу данных по умолчанию, поэтому таблицу `django_session` создают первые миграции фреймворка.
Чтобы инициализировать её, выполните в корне проекта:

```bash
python manage.py migrate            # применяет все доступные миграции, включая сессии
# при необходимости можно отдельно выполнить миграцию приложения sessions:
python manage.py migrate sessions
```

После выполнения команды таблица появится в выбранной базе данных (значение `DATABASES['default']`, обычно PostgreSQL),
и ошибки `no such table: django_session` больше не будет.

## Тесты и проверки

```bash
python manage.py check
python manage.py test
```

## Развёртывание на Render.com

Проект готов к запуску на Render как web service. Репозиторий содержит файл [`render.yaml`](render.yaml),
который описывает инфраструктуру (Python‑сервис + PostgreSQL). Есть два варианта деплоя:

### 1. Через Blueprint (рекомендуется)

1. Создайте новый Blueprint на Render и укажите URL форка.
2. Render считает `render.yaml` и создаст:
   - web‑сервис `zetom` с билд-командой `pip install ...`, сборкой статики и миграциями;
   - базу данных `zetom-db` (PostgreSQL Free plan).
3. После создания дождитесь окончания билда и нажмите **Manual Deploy** → **Deploy latest commit**.

### 2. Ручная настройка Web Service

1. Создайте PostgreSQL базу на Render и скопируйте значение переменной `Internal Database URL`.
2. Создайте **Web Service → Build & deploy from repository**.
3. Укажите команды:
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py compilemessages`
   - **Start Command**: `gunicorn zetom_project.wsgi:application`
4. Добавьте переменные окружения:
   - `PYTHON_VERSION=3.11.9`
   - `DJANGO_SECRET_KEY` — сгенерируйте безопасное значение (можно через Render `Generate`).
   - `DJANGO_DEBUG=false`
   - `DJANGO_ALLOWED_HOSTS=<app-name>.onrender.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<app-name>.onrender.com`
   - `DATABASE_URL` — строка подключения к Render PostgreSQL.
   - (опционально) `DEFAULT_LANGUAGE`, `SMTP_*`.
5. После деплоя зайдите по адресу `https://<app-name>.onrender.com/` и проверьте, что всё работает.

### Что происходит под капотом

- `dj-database-url` автоматически переключает проект на PostgreSQL, когда Render задаёт `DATABASE_URL`.
- WhiteNoise обслуживает статику, собранную командой `collectstatic`.
- `render.yaml` хранит все необходимые команды и переменные, так что повторный деплой требует лишь коммитов в репозиторий.

## Дополнительно

- Панель находится по адресу `/panel/`, логиниться нужно через `/login/`.
- Для тестовой работы с админ‑панелью создавайте/обновляйте пользователей через команду `create_admin_user`,
  а в продакшене — через модуль Settings. Команда печатает выданный пароль в консоль, не сохраняйте его в Git
  и удаляйте после использования.
- Для отладки писем без SMTP включите консольный backend (по умолчанию в `DEBUG=true`).
- В продакшене Django автоматически включает строгие флаги безопасности, если `DJANGO_DEBUG=false`.
