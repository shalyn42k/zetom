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

Небольшое Django‑приложение с контактной формой, переводами интерфейса и простым кабинетом управления сообщениями.
Авторизация в панели строится на базе таблицы пользователей, поэтому пароль хранится в БД, а не в `.env`.

## Что делает проект

- показывает контактную форму и список входящих сообщений;
- может отправлять письма через SMTP (опционально);
- поддерживает PDF‑отчёты и переводы интерфейса.

## Требования

- Python 3.11+;
- PostgreSQL 14+ (можно через Docker);
- pip и virtualenv/venv;
- (опционально) SMTP‑учётка для реальной отправки почты.

## Быстрый старт локально (без Docker)

1. Склонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone <your-fork-url>
   cd zetom
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Скопируйте `.env.example` в `.env` и заполните значения. Важные переменные:
   - `DJANGO_SECRET_KEY` — любой длинный случайный ключ.
   - `DJANGO_DEBUG` — `true` для разработки.
   - `DJANGO_ALLOWED_HOSTS` — список доменов через запятую.
   - `DATABASE_URL` **или** `POSTGRES_*` — строка подключения к PostgreSQL (обязательна для работы).
   - `LEGACY_SQLITE_PATH` — путь к существующей SQLite базе, если нужно перенести данные.
   - `SMTP_*` — настройки SMTP, если нужна отправка писем.
   - `DJANGO_ALLOW_SQLITE_FALLBACK` — только для локальной отладки без PostgreSQL; не используйте в проде.

5. Примените миграции и (по необходимости) соберите статику на PostgreSQL:
   ```bash
   python manage.py migrate
   python manage.py collectstatic  # можно пропустить в dev
   ```

6. Создайте учётку для входа в админ‑панель (только для разработки/test):
   ```bash
   python manage.py create_admin_user you@example.com --level level1
   ```
   Команда попросит ввести пароль (или сгенерирует случайный, если оставить пустым) и сохранит его хеш в базе.
   При необходимости переопределите уровень доступа (`level1`, `level2`, `level3`) и используйте `--force-update`,
   чтобы обновить существующую запись. Чтобы задать свой тестовый пароль вручную, добавьте флаг `--password <VALUE>` —
   пароль будет захеширован и сохранён только в базе данных.

   Если команда сообщает об отсутствии колонок, значит база данных не прошла актуальные миграции — выполните
   `python manage.py migrate` ещё раз и убедитесь, что подключены к правильной PostgreSQL базе. Не коммитьте тестовые
   пароли и не храните их в репозитории.

7. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

8. Команды для быстрого запуска сервера после удаления БД (нужно только указать пароль):
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py create_admin_user test@gmail.com --level level1
   ```

Приложение будет доступно на <http://127.0.0.1:8000/>. Язык интерфейса переключается параметром `?lang=en` / `?lang=pl`.

## Запуск в Docker (самый простой способ)

В репозитории есть `docker-compose.yml`, который поднимает PostgreSQL и Django‑сервер сразу.

1. При необходимости поправьте логин/пароль БД в `docker-compose.yml`:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` в сервисе `db`;
   - строку `DATABASE_URL` в сервисе `web` (должна соответствовать значениям выше).

2. Поднимите контейнеры:
   ```bash
   docker compose up --build
   ```

3. В другом терминале примените миграции и создайте пользователя:
   ```bash
   docker exec -it zetom_app python manage.py migrate
   docker exec -it zetom_app python manage.py create_admin_user test@gmail.com --level level1
   ```

После этого сервер будет доступен на <http://localhost:8888/>.

## Запуск в Docker вручную (без compose)

1. Скопируйте `.env.example` в `.env` и укажите `DATABASE_URL` PostgreSQL (или `POSTGRES_*`).
   Пример для локального docker‑контейнера: `postgresql://zetom:zetom@zetom-db:5432/zetom`.

2. Поднимите PostgreSQL (пример для сети `zetom-net`):
   ```bash
   docker network create zetom-net
   docker run -d --name zetom-db --network zetom-net -e POSTGRES_DB=zetom -e POSTGRES_USER=zetom -e POSTGRES_PASSWORD=zetom postgres:16
   ```

3. Соберите образ приложения:
   ```bash
   docker build -t zetom:local .
   ```

4. Запустите контейнер, подключив `.env` и сеть с базой:
   ```bash
   docker run --rm --env-file .env --network zetom-net -p 8888:8888 zetom:local
   ```

5. Примените миграции и создайте учётку администратора (при необходимости):
   ```bash
   docker exec -it ИМЯ_ВАШЕГО_КОНТЕЙНЕРА python manage.py migrate
   docker exec -it ИМЯ_ВАШЕГО_КОНТЕЙНЕРА python manage.py create_admin_user test@gmail.com --level level1
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

## Перенос данных из SQLite в PostgreSQL

1. Настройте подключение к PostgreSQL через `DATABASE_URL` или `POSTGRES_*` в `.env`.
   База должна быть пустой (новая или очищенная).
2. Укажите путь к старой базе SQLite через `LEGACY_SQLITE_PATH` (например, `LEGACY_SQLITE_PATH=/app/db.sqlite3`).
3. Выполните миграции для новой базы:
   ```bash
   python manage.py migrate
   ```
4. Запустите перенос данных:
   ```bash
   python manage.py migrate_sqlite_to_postgres --force-flush
   ```
   Флаг `--force-flush` очищает данные в целевой базе перед импортом (используйте только если база новая и данных нет).
   Команда валидирует, что основная БД — PostgreSQL, и скопирует все строки, восстанавливая последовательности.
5. Перенесите каталог `media/`, если в SQLite базе есть связанные загрузки файлов.
6. Проверьте систему:
   ```bash
   python manage.py check
   python manage.py test
   ```

Для локальной отладки без PostgreSQL можно временно включить `DJANGO_ALLOW_SQLITE_FALLBACK=true`,
но миграцию данных выполняйте только в PostgreSQL.

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
