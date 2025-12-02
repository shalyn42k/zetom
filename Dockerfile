# Lightweight Python image suitable for Django apps
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=true \
    DJANGO_ALLOWED_HOSTS=0.0.0.0,localhost,127.0.0.1 \
    DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8888,http://127.0.0.1:8888,http://0.0.0.0:8888

WORKDIR /app

# System packages for psycopg2-binary and building wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && pip install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888

CMD ["python", "manage.py", "runserver", "0.0.0.0:8888"]
