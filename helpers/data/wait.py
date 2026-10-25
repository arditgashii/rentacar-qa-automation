import time
from collections.abc import Callable


def wait_until[T](
    check: Callable[[], T | None],
    timeout: float,
    message: str | Callable[[], str],
    interval: float = 0.5,
) -> T:
    """Calls `check` until it returns something truthy, or fails after `timeout` seconds.

    `message` can be a function, so the failure can describe the last thing that was seen.
    """
    deadline = time.monotonic() + timeout
    while True:
        result = check()
        if result:
            return result
        if time.monotonic() > deadline:
            text = message() if callable(message) else message
            raise AssertionError(f"{text} (waited {timeout:g} s)")
        time.sleep(interval)
