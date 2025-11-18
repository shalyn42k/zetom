#!/usr/bin/env python
import os
import sys

try:
    from dotenv import load_dotenv  # pip install python-dotenv
except ModuleNotFoundError:  # optional dependency
    load_dotenv = None


def main() -> None:
    # Подтягиваем переменные из .env в корне проекта (рядом с manage.py)
    if load_dotenv is not None:
        # Без аргументов load_dotenv сам ищет .env рядом с manage.py
        load_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zetom_project.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is it installed and on PYTHONPATH? "
            "Did you forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
