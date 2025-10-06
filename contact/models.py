from django.db import models
from django.utils import timezone


class ContactMessage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    company = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"
