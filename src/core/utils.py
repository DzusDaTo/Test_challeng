import json

from .models import Outbox
from .tasks import process_outbox


def log_event(event_type, event_context):
    Outbox.objects.create(
        event_type=event_type,
        event_context=json.dumps(event_context),
    )

    process_outbox.delay()
