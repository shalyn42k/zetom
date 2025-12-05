"""Fill empty PO entries using deep-translator for Ukrainian locale."""
from pathlib import Path

import polib
from deep_translator import GoogleTranslator
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Auto-translate empty msgstr values (defaults to Ukrainian) using GoogleTranslator."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=settings.LANGUAGE_CODE,
            help="Source language code (defaults to settings.LANGUAGE_CODE)",
        )
        parser.add_argument(
            "--target",
            default="uk",
            help="Target language code (defaults to 'uk')",
        )
        parser.add_argument(
            "--locale-paths",
            nargs="*",
            help="Optional custom locale roots; defaults to settings.LOCALE_PATHS",
        )

    def handle(self, *args, **options):
        source_language = options["source"]
        target_language = options["target"]
        locale_roots = options["locale_paths"] or list(settings.LOCALE_PATHS) or [
            settings.BASE_DIR / "locale"
        ]

        translator = GoogleTranslator(source=source_language, target=target_language)

        for locale_root in locale_roots:
            root_path = Path(locale_root)
            if not root_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"Skipping missing locale path: {root_path}")
                )
                continue

            po_files = list((root_path / target_language / "LC_MESSAGES").glob("*.po"))
            if not po_files:
                self.stdout.write(
                    self.style.WARNING(
                        f"No .po files found for language '{target_language}' under {root_path}"
                    )
                )
                continue

            for po_path in po_files:
                po = polib.pofile(po_path)
                updated = 0
                for entry in po:
                    if entry.obsolete:
                        continue

                    if entry.msgid_plural:
                        for idx, msgstr in entry.msgstr_plural.items():
                            if not msgstr:
                                base_text = entry.msgid if idx == "0" else entry.msgid_plural
                                entry.msgstr_plural[idx] = translator.translate(base_text)
                                updated += 1
                    elif not entry.msgstr:
                        entry.msgstr = translator.translate(entry.msgid)
                        updated += 1

                if updated:
                    po.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated {updated} translation entries in {po_path}"
                        )
                    )
                else:
                    self.stdout.write(f"No empty translations in {po_path}")
