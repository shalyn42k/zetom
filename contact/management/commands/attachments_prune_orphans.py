from __future__ import annotations

from django.core.management.base import BaseCommand

from ...models import Attachment


class Command(BaseCommand):
    help = "Remove attachment records whose files no longer exist on storage."

    def handle(self, *args, **options):
        storage = Attachment._meta.get_field("file").storage
        removed = 0
        for attachment in Attachment.objects.all().iterator():
            if not attachment.file.name:
                attachment.delete()
                removed += 1
                continue
            if not storage.exists(attachment.file.name):
                self.stdout.write(
                    self.style.WARNING(
                        f"Deleting orphaned attachment #{attachment.pk} ({attachment.original_name})"
                    )
                )
                attachment.delete()
                removed += 1
        if removed:
            self.stdout.write(self.style.SUCCESS(f"Removed {removed} orphaned attachments."))
        else:
            self.stdout.write("No orphaned attachments found.")
