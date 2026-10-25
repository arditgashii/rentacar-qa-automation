"""Unique test data, so parallel workers and repeated runs never collide."""

import itertools
import time

from config.settings import worker_index

# Every name this suite creates starts with AUTO, so leftovers are easy to find.
AUTO_PREFIX = "AUTO"
_counter = itertools.count()


def _stamp() -> str:
    return f"{int(time.time() * 1000) % 10**9}{worker_index()}{next(_counter) % 10}"


def unique_name(test_case: str, label: str) -> str:
    """`unique_name("TC-004", "Car")` gives `AUTO TC-004 Car 4812934120`."""
    return f"{AUTO_PREFIX} {test_case} {label} {_stamp()}"


def unique_plate() -> str:
    """A license plate that matches the platform rules: letters, digits, spaces, hyphens."""
    return f"AUTO {_stamp()}"


def unique_email(test_case: str) -> str:
    return f"auto.{test_case.lower()}.{_stamp()}@drivenow.test"


def unique_city(test_case: str) -> str:
    """A city nobody else uses, so a search returns only the cars this test created."""
    return f"{AUTO_PREFIX} {test_case} City {_stamp()}"
