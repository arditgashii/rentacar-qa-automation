"""Peeks the `audit` subscription of the booking topic to prove an event was published.

Peeking does not remove messages, so it never competes with the platform's worker, which reads the
`notifications` subscription.
"""

import json
from typing import Any

from azure.servicebus import ServiceBusClient

from config.settings import get_settings


def service_bus_configured() -> bool:
    return bool(get_settings().servicebus_connection_string)


def find_booking_event(booking_id: int, event_type: str) -> dict[str, Any] | None:
    settings = get_settings()
    with ServiceBusClient.from_connection_string(settings.servicebus_connection_string) as client:
        receiver = client.get_subscription_receiver(settings.booking_topic, settings.audit_subscription)
        with receiver:
            sequence = 0
            while True:
                messages = receiver.peek_messages(max_message_count=100, sequence_number=sequence)
                if not messages:
                    return None
                for message in messages:
                    event = json.loads(str(message))
                    if event.get("booking_id") == booking_id and event.get("type") == event_type:
                        return event
                sequence = (messages[-1].sequence_number or 0) + 1
