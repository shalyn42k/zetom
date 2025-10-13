from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    # Новый, удобный enum для статусов (для кода и сидера)
    class Status(models.TextChoices):
        NEW = "new", "new"
        IN_PROGRESS = "in_progress", "in_progress"
        READY = "ready", "ready"

    # Старые константы оставляем для совместимости
    STATUS_NEW = Status.NEW
    STATUS_IN_PROGRESS = Status.IN_PROGRESS
    STATUS_READY = Status.READY

    STATUS_CHOICES = Status.choices  # тоже оставим, если где-то используется

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50)
    message = models.TextField()

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"
