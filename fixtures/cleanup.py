"""`cleanup` removes everything a test registered, after the test, passed or failed.

Register right after creating something: `cleanup.car(car["id"])`. Items are removed newest first
through the API with an admin account. A failed removal fails the test, so leftovers never go
unnoticed. Run with KEEP_DATA=1 to keep the data, for example to look at it after a run.
"""

from collections.abc import Callable, Iterator

import pytest

from config.settings import get_settings, lease_account
from helpers.api.client import ApiClient, api_login
from helpers.cars.api import delete_car_via_api
from helpers.users.api import deactivate_user_via_api

Remover = Callable[[ApiClient, int], None]


class Cleanup:
    def __init__(self) -> None:
        self._items: list[tuple[Remover, int]] = []

    def car(self, car_id: int) -> None:
        """Deletes the car (with its photos and bookings) after the test."""
        self._items.append((delete_car_via_api, car_id))

    def user(self, user_id: int) -> None:
        """Deactivates the user after the test (users cannot be deleted)."""
        self._items.append((deactivate_user_via_api, user_id))

    def run(self) -> None:
        if not self._items:
            return
        admin = api_login(lease_account("admin"))
        try:
            for remove, item_id in reversed(self._items):
                remove(admin, item_id)
        finally:
            admin.close()


@pytest.fixture
def cleanup() -> Iterator[Cleanup]:
    items = Cleanup()
    yield items
    if not get_settings().keep_data:
        items.run()
