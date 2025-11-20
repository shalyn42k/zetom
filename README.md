# Zetom Django Project

Небольшое Django‑приложение с контактной формой, переводами и простым "админ"‑кабинетом. Авторизация в панели теперь строится на базе таблицы пользователей (управляется в модуле Settings), поэтому пароль хранится в базе данных, а не в `.env`.

## Возможности

- вывод контактной формы и списка входящих сообщений;
- отправка писем через SMTP (опционально);
- формирование PDF, перевод интерфейса.

## Требования

- Python 3.11+;
- pip и virtualenv/venv;
- (опционально) SMTP‑учётка для реальной отправки почты.

## Быстрый старт локально

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
   - `SQLITE_NAME` — путь к SQLite базе (по умолчанию `db.sqlite3`).
   - `SMTP_*` — настройки SMTP, если нужна отправка писем.

5. Примените миграции и (по необходимости) соберите статику:
   ```bash
   python manage.py migrate
   python manage.py collectstatic  # можно пропустить в dev
   ```

6. Создайте учётку для входа в админ‑панель (только для разработки/test):
   ```bash
   python manage.py create_admin_user you@example.com --level level1
   ```
   Команда попросит ввести пароль (или сгенерирует случайный, если оставить пустым) и сохранит его хеш в базе. При необходимости переопределите уровень доступа (`level1`, `level2`, `level3`) и используйте `--force-update`, чтобы обновить существующую запись. Чтобы задать свой тестовый пароль вручную, добавьте флаг `--password <VALUE>` — пароль будет захеширован и сохранён только в базе данных.

   Если появилось сообщение `no such column: contact_adminuser.password_hash`, значит у вас старая база без актуальных миграций. Удалите устаревший файл SQLite или примените миграции к нужной БД и повторите команды:

   ```bash
   python manage.py migrate
   ```
   Это гарантированно создаст таблицу с колонкой `password_hash` и заведёт тестовый логин. Не коммитьте тестовые пароли и не храните их в репозитории.

7. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```
8. Команды для быстрого запуска сервера после удаления дб(вам написать только пароль):
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py create_admin_user test@gmail.com --level level1
   ```
Приложение будет доступно на <http://127.0.0.1:8000/>. Язык интерфейса переключается параметром `?lang=en` / `?lang=pl`.

## Тесты и проверки

```bash
python manage.py check
python manage.py test
```

## Развёртывание на Render.com

Проект готов к запуску на Render как web service. Репозиторий содержит файл [`render.yaml`](render.yaml), который описывает инфраструктуру (Python‑сервис + PostgreSQL). Есть два варианта деплоя:

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
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
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
- Для тестовой работы с админ‑панелью создавайте/обновляйте пользователей через команду `create_admin_user`, а в продакшене — через модуль Settings. Команда печатает выданный пароль в консоль, не сохраняйте его в Git и удаляйте после использования.
- Для отладки писем без SMTP включите консольный backend (по умолчанию в `DEBUG=true`).
- В продакшене Django автоматически включает строгие флаги безопасности, если `DJANGO_DEBUG=false`.
