# Zetom Django Project

Небольшое Django‑приложение с контактной формой, публичным просмотром заявок по одноразовому токену и кабинетом сотрудников (используется стандартная авторизация Django).

## Возможности

- вывод контактной формы и списка входящих сообщений;
- отправка писем через SMTP (опционально);
- формирование PDF, перевод интерфейса;
- управление отделами и ролями сотрудников (ADMIN/EMPLOYEE) с автоматическим ограничением доступа к заявкам;
- доступ клиентов к своим заявкам по уникальной ссылке с токеном;
- загрузка нескольких вложений с проверкой размера и типов файлов.

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
   - `ATTACH_MAX_SIZE_MB` — максимальный суммарный размер вложений (по умолчанию 25 МБ).
   - `ATTACH_ALLOWED_TYPES` — разрешённые MIME-типы через запятую (по умолчанию PDF/JPG/PNG/TXT).
   - `ALLOW_PUBLIC_EDITS` — разрешить ли заявителю добавлять финальные комментарии/файлы (по умолчанию `false`).
   - `SMTP_*` — настройки SMTP, если нужна отправка писем.

5. Примените миграции и (по необходимости) соберите статику:
   ```bash
   python manage.py migrate
   python manage.py collectstatic  # можно пропустить в dev
   ```

6. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

Приложение будет доступно на <http://127.0.0.1:8000/>. Язык интерфейса переключается параметром `?lang=en` / `?lang=pl`.

### Работа со служебным кабинетом

- Создайте пользователей через Django Admin или shell (`createsuperuser`).
- Назначьте роли и отделы на странице `/staff/users/` (доступна только ADMIN).
- Сотрудники с ролью EMPLOYEE видят только заявки своего отдела.

### Публичные ссылки на заявки

- После отправки формы заявитель получает ID и токен доступа.
- Публичная страница заявки доступна по адресу `/r/<id>/` с параметром `?access=<token>`.
- При отключённом `ALLOW_PUBLIC_EDITS` страница отображает только детали и вложения.

### Обслуживание вложений

- Загрузить несколько файлов можно как заявителю, так и сотруднику.
- Для очистки записей без файлов выполните команду:

  ```bash
  python manage.py attachments_prune_orphans
  ```

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
   - `ADMIN_PASSWORD` — пароль для панели.
   - (опционально) `DEFAULT_LANGUAGE`, `SMTP_*`.
5. После деплоя зайдите по адресу `https://<app-name>.onrender.com/` и проверьте, что всё работает.

### Что происходит под капотом

- `dj-database-url` автоматически переключает проект на PostgreSQL, когда Render задаёт `DATABASE_URL`.
- WhiteNoise обслуживает статику, собранную командой `collectstatic`.
- `render.yaml` хранит все необходимые команды и переменные, так что повторный деплой требует лишь коммитов в репозиторий.

## Дополнительно

- Служебный кабинет доступен по адресу `/staff/requests/`, страница входа — `/staff/login/`.
- Для отладки писем без SMTP включите консольный backend (по умолчанию в `DEBUG=true`).
- В продакшене Django автоматически включает строгие флаги безопасности, если `DJANGO_DEBUG=false`.
