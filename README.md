# Zetom Django Project

This project provides a simple contact form and admin panel implemented with Django and SQLite by default.

## Prerequisites

- Python 3.11+
- (Optional) A SMTP account if you want outbound email notifications

## Initial setup

1. **Clone and enter the repository**
   ```bash
   git clone <your-fork-url>
   cd zetom
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Copy `.env.example` to `.env` and adjust values as needed. The important ones are:
   - `DJANGO_SECRET_KEY`: any random string for cryptographic signing.
   - `SQLITE_DB_PATH`: optional path to the SQLite database file (defaults to `<project>/db.sqlite3`).
     If you provide a custom path, the parent folder will be created automatically when Django starts.
   - `ADMIN_PASSWORD`: password used to access the admin panel at `/login/`.
   - `SMTP_*`: mail server settings if you want to send emails.

   Django will read these variables from the environment. If you use a tool like [direnv](https://direnv.net/) or export them manually, ensure they are available before running management commands. You can also load the `.env` file with `export $(cat .env | xargs)` on Unix shells.

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Collect static files (optional for local development)**
   ```bash
   python manage.py collectstatic
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

   The site is now reachable at <http://127.0.0.1:8000/>. Append `?lang=en` or `?lang=pl` to toggle languages.

## Admin panel login

The admin panel lives at `/panel/`. Sign in via `/login/` with the password supplied in the `ADMIN_PASSWORD` environment variable. Successful authentication sets a session cookie; there is no Django admin user required.

## Sending emails

Outbound emails are optional. If SMTP credentials are provided, the contact form will notify the sender, and the admin panel's "send email" form will use the same server.

## Running tests and checks

```bash
python manage.py check
```

Add your own tests and run them with `python manage.py test`.
