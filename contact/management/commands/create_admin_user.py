from __future__ import annotations

import getpass
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from contact.models import AdminUser


class Command(BaseCommand):
    help = "Create or update an admin-panel user with the given email/password."

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument("email", help="Email for the admin-panel user")
        parser.add_argument(
            "--password",
            help=(
                "Plaintext password to set. If omitted, you'll be prompted; "
                "empty input will generate a random secure token."
            ),
        )
        parser.add_argument(
            "--level",
            choices=[
                AdminUser.LEVEL_ADMIN,
                AdminUser.LEVEL_DEPARTMENT,
                AdminUser.LEVEL_TESTER,
            ],
            default=AdminUser.LEVEL_ADMIN,
            help="Access level to assign (default: level1)",
        )
        parser.add_argument(
            "--force-update",
            action="store_true",
            help="Update an existing user even if it is already present.",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        email: str = options["email"].strip()
        password_opt: str | None = options.get("password")
        level: str = options["level"]
        force_update: bool = options["force_update"]

        if not email:
            raise CommandError("Email must not be empty")

        password = password_opt
        if password is None:
            self.stdout.write("Enter password (leave empty to auto-generate): ", ending="")
            self.stdout.flush()
            password = getpass.getpass("")

        if not password:
            from contact.models import _generate_access_token  # local import avoids circular

            password = _generate_access_token()
            self.stdout.write(self.style.NOTICE("Generated random password token."))

        user, created = AdminUser.objects.get_or_create(
            email__iexact=email,
            defaults={
                "email": email,
                "password_hash": "",
                "level_of_access": level,
                "departments": [],
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["email", "password_hash", "level_of_access", "departments", "updated_at"])
            action = "created"
        else:
            if not force_update:
                raise CommandError(
                    "User already exists. Re-run with --force-update to change password/level."
                )
            user.email = email
            user.level_of_access = level
            if level != AdminUser.LEVEL_DEPARTMENT:
                user.departments = []
            user.set_password(password)
            user.save(update_fields=["email", "level_of_access", "departments", "password_hash", "updated_at"])
            action = "updated"

        self.stdout.write(self.style.SUCCESS(f"Admin user {action}: {user.email} ({user.level_of_access})"))
        self.stdout.write(self.style.WARNING("Store this password securely; it will not be shown again."))
        self.stdout.write(password)
        return None
