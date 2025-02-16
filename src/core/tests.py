import pytest
from django.utils import timezone
from .models import Outbox
from .event_log_client import log_event
from clickhouse_driver import Client
from unittest.mock import patch
from celery.exceptions import MaxRetriesExceededError
from .tasks import process_outbox
pytestmark = pytest.mark.django_db


def test_log_event_creates_outbox_entry():
    event_type = 'create_user'
    event_context = {'user_id': 1, 'user_email': 'test@example.com'}

    event_date_time_before = timezone.now()

    log_event(event_type, event_context)

    outbox_entry = Outbox.objects.first()
    assert outbox_entry is not None
    assert outbox_entry.event_type == event_type
    assert outbox_entry.event_context == '{"user_id": 1, "user_email": "test@example.com"}'
    assert outbox_entry.processed is False

    assert event_date_time_before <= outbox_entry.event_date_time <= timezone.now()


def test_log_event_creates_multiple_entries():
    log_event('create_user', {'user_id': 1, 'user_email': 'test@example.com'})
    log_event('update_user', {'user_id': 1, 'user_email': 'newemail@example.com'})

    outbox_entries = Outbox.objects.all()
    assert outbox_entries.count() == 2
    assert outbox_entries[0].event_type == 'create_user'
    assert outbox_entries[1].event_type == 'update_user'


def test_log_event_records_in_clickhouse():
    event_type = 'create_user'
    event_context = {'user_id': 1, 'user_email': 'test@example.com'}

    event_date_time_before = timezone.now()

    log_event(event_type, event_context)

    client = Client('clickhouse')

    result = client.execute('SELECT * FROM events_table WHERE event_type = %s', (event_type,))

    assert len(result) > 0
    assert result[0][0] == event_type
    assert result[0][2] == '{"user_id": 1, "user_email": "test@example.com"}'

    event_date_time_in_ch = result[0][1]
    assert event_date_time_before <= event_date_time_in_ch <= timezone.now()


def test_log_event_handles_clickhouse_error():
    event_type = 'create_user'
    event_context = {'user_id': 1, 'user_email': 'test@example.com'}

    with patch.object(Client, 'execute', side_effect=Exception('ClickHouse connection failed')):
        try:
            log_event(event_type, event_context)
        except Exception as e:
            assert str(e) == 'ClickHouse connection failed'


def test_process_outbox_retries_on_error():
    with patch('your_project.tasks.Client.insert', side_effect=Exception('ClickHouse connection failed')):
        with pytest.raises(MaxRetriesExceededError):
            process_outbox.retry()
