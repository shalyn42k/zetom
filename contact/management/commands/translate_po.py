"""Auto-translate .po files using free translation providers."""
from pathlib import Path

import polib
from deep_translator import GoogleTranslator
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fill empty msgstr entries in .po files via GoogleTranslator."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=settings.LANGUAGE_CODE,
            help="Source language code (defaults to settings.LANGUAGE_CODE)",
        )
        parser.add_argument(
            "--languages",
            nargs="*",
            help="Target language codes (defaults to all LANGUAGES except source)",
        )
        parser.add_argument(
            "--locale-paths",
            nargs="*",
            help="Custom locale roots (defaults to settings.LOCALE_PATHS or BASE_DIR/locale)",
        )

    def handle(self, *args, **options):
        source_language = options["source"]
        target_languages = options["languages"] or [
            code for code, _ in settings.LANGUAGES if code != source_language
        ]
        locale_roots = options["locale_paths"] or list(settings.LOCALE_PATHS) or [
            settings.BASE_DIR / "locale"
        ]

        for locale_root in locale_roots:
            root_path = Path(locale_root)
            if not root_path.exists():
                self.stdout.write(
                    self.style.WARNING(f"Skipping missing locale path: {root_path}")
                )
                continue

            for language in target_languages:
                po_files = list((root_path / language / "LC_MESSAGES").glob("*.po"))
                if not po_files:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No .po files found for language '{language}' under {root_path}"
                        )
                    )
                    continue

                translator = GoogleTranslator(source=source_language, target=language)

                for po_path in po_files:
                    po = polib.pofile(po_path)
                    updated_entries = 0

                    for entry in po:
                        if entry.obsolete:
                            continue

                        if entry.msgid_plural:
                            for idx, msgstr in entry.msgstr_plural.items():
                                if not msgstr:
                                    base_text = entry.msgid if idx == "0" else entry.msgid_plural
                                    entry.msgstr_plural[idx] = translator.translate(base_text)
                                    updated_entries += 1
                        elif not entry.msgstr:
                            entry.msgstr = translator.translate(entry.msgid)
                            updated_entries += 1

                    if updated_entries:
                        po.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated {updated_entries} entries in {po_path}"
                            )
                        )
                    else:
                        self.stdout.write(f"No empty translations in {po_path}")
