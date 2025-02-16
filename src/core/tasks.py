from celery import shared_task
from clickhouse_driver import Client
from .models import Outbox


@shared_task
def process_outbox():
    outbox_entries = Outbox.objects.filter(processed=False)[:100]  # Максимум 100 событий за раз

    client = Client('clickhouse')

    data = []
    for entry in outbox_entries:
        data.append({
            'event_type': entry.event_type,
            'event_date_time': entry.event_date_time,
            'environment': entry.environment,
            'event_context': entry.event_context,
            'metadata_version': entry.metadata_version,
        })

    client.insert('events_table', data)

    outbox_entries.update(processed=True)
