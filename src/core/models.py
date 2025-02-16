from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None, # noqa
    ) -> None:
        # https://docs.djangoproject.com/en/5.1/ref/models/fields/#django.db.models.DateField.auto_now
        self.updated_at = timezone.now()

        if isinstance(update_fields, list):
            update_fields.append('updated_at')
        elif isinstance(update_fields, set):
            update_fields.add('updated_at')

        super().save(force_insert, force_update, using, update_fields)


class Outbox(models.Model):
    EVENT_TYPE_CHOICES = [
        ('create_user', 'Create User'),
        ('update_user', 'Update User'),
    ]

    event_type = models.CharField(max_length=255, choices=EVENT_TYPE_CHOICES)
    event_date_time = models.DateTimeField(auto_now_add=True)
    environment = models.CharField(max_length=50, default='production')
    event_context = models.JSONField(default=dict)
    metadata_version = models.BigIntegerField(default=1)
    processed = models.BooleanField(default=False) 

    def __str__(self):
        return f'{self.event_type} at {self.event_date_time}'