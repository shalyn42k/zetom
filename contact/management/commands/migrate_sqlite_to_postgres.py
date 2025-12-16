from __future__ import annotations

import io
import tempfile
from typing import Iterable

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management import BaseCommand, CommandError, call_command
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = (
        "Copy all data from the legacy SQLite database (configured via LEGACY_SQLITE_PATH) "
        "into the default PostgreSQL database."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Print a progress marker every N imported objects (verbosity >= 2).",
        )
        parser.add_argument(
            "--force-flush",
            action="store_true",
            help=(
                "Flush the default database before importing. Use when the target already contains "
                "data from previous runs."
            ),
        )
        parser.add_argument(
            "--skip-sequence-reset",
            action="store_true",
            help="Do not reset PostgreSQL sequences after import (not recommended).",
        )

    def handle(self, *args, **options):  # type: ignore[override]
        default_alias = DEFAULT_DB_ALIAS
        legacy_alias = "legacy_sqlite"
        batch_size: int = options["batch_size"]
        force_flush: bool = options["force_flush"]
        skip_sequence_reset: bool = options["skip_sequence_reset"]

        self._validate_connections(default_alias, legacy_alias)
        self._ensure_target_is_empty(default_alias, force_flush)

        imported = 0
        with tempfile.SpooledTemporaryFile(max_size=5_000_000, mode="w+", encoding="utf-8") as dump_stream:
            call_command(
                "dumpdata",
                stdout=dump_stream,
                database=legacy_alias,
                use_natural_foreign_keys=True,
                use_base_manager=True,
            )

            dump_stream.seek(0)

            with transaction.atomic(using=default_alias):
                for imported, obj in enumerate(
                    serializers.deserialize("json", dump_stream, use_natural_foreign_keys=True), start=1
                ):
                    obj.save(using=default_alias)
                    if self.verbosity >= 2 and imported % batch_size == 0:
                        self.stdout.write(f"Imported {imported} objects so far...")

        if not skip_sequence_reset:
            self._reset_sequences(default_alias)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import finished. {imported or 0} objects copied from SQLite to PostgreSQL. "
                "Remember to move uploaded files from MEDIA_ROOT if needed."
            )
        )

    def _validate_connections(self, default_alias: str, legacy_alias: str) -> None:
        if default_alias not in settings.DATABASES:
            raise CommandError("Default database is not configured.")

        default_engine = settings.DATABASES[default_alias].get("ENGINE", "")
        if "postgresql" not in default_engine:
            raise CommandError(
                "Default database must be PostgreSQL before running this command. "
                "Update DATABASE_URL/POSTGRES_* and re-run migrations."
            )

        legacy_db = settings.DATABASES.get(legacy_alias)
        if not legacy_db:
            raise CommandError(
                "Legacy SQLite connection is missing. Set LEGACY_SQLITE_PATH to the existing db.sqlite3 file."
            )
        if not legacy_db.get("ENGINE", "").endswith("sqlite3"):
            raise CommandError("Legacy database must use the SQLite engine.")

        for alias in (legacy_alias, default_alias):
            try:
                connections[alias].ensure_connection()
            except OperationalError as exc:  # pragma: no cover - defensive guard
                raise CommandError(f"Unable to connect to database '{alias}': {exc}") from exc

    def _ensure_target_is_empty(self, alias: str, force_flush: bool) -> None:
        non_empty_tables = list(self._iter_non_empty_models(alias))
        if non_empty_tables and not force_flush:
            table_names = ", ".join(non_empty_tables[:3])
            raise CommandError(
                "Default database already has data. Run with --force-flush to clear it first "
                f"or start with a fresh PostgreSQL schema. Sample tables with data: {table_names}"
            )

        if non_empty_tables and force_flush:
            call_command(
                "flush",
                database=alias,
                interactive=False,
                inhibit_post_migrate=True,
            )

    def _iter_non_empty_models(self, alias: str) -> Iterable[str]:
        for model in apps.get_models():
            if not model._meta.managed:
                continue
            if model._meta.db_table == "django_migrations":
                continue
            if model.objects.using(alias).exists():
                yield model._meta.label_lower

    def _reset_sequences(self, alias: str) -> None:
        connection = connections[alias]
        if connection.vendor != "postgresql":
            return

        sql_stream = io.StringIO()
        app_labels = {config.label for config in apps.get_app_configs() if any(config.get_models())}
        call_command("sqlsequencereset", *sorted(app_labels), database=alias, stdout=sql_stream)
        sql_stream.seek(0)
        statements = [
            statement.strip()
            for statement in sql_stream.read().split(";")
            if statement.strip()
        ]

        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
