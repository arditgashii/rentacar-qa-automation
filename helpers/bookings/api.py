from datetime import date, timedelta
from typing import Any

import httpx

from helpers.api.client import ApiClient


def days_from_today(days: int) -> date:
    return date.today() + timedelta(days=days)


def book_car_via_api(api: ApiClient, car_id: int, start: date, end: date) -> httpx.Response:
    """Sends the booking and returns the raw response, so a test can check refusals too."""
    payload = {"car_id": car_id, "start_date": start.isoformat(), "end_date": end.isoformat()}
    return api.post("/bookings", json=payload, expected=None)


def notifications_for_booking(api: ApiClient, booking_id: int) -> list[dict[str, Any]]:
    notifications = api.get("/notifications").json()
    return [n for n in notifications if n["payload"].get("booking_id") == booking_id]
