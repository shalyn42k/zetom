from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "ready"

    STATUS_CHOICES = [
        (STATUS_NEW, "new"),
        (STATUS_IN_PROGRESS, "in_progress"),
        (STATUS_READY, "ready"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50)
    message = models.TextField()
    final_changes = models.TextField(blank=True)
    final_response = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"


class ContactMessageRevision(models.Model):
    EDITOR_USER = "user"
    EDITOR_ADMIN = "admin"

    EDITOR_CHOICES = (
        (EDITOR_USER, "user"),
        (EDITOR_ADMIN, "admin"),
    )

    message = models.ForeignKey(
        ContactMessage,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    editor = models.CharField(max_length=16, choices=EDITOR_CHOICES, db_index=True)
    previous_data = models.JSONField(default=dict)
    new_data = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Revision {self.pk} for message #{self.message_id}"
