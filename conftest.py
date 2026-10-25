from typing import Any

import pytest
from playwright.sync_api import expect

from config.settings import get_settings

pytest_plugins = ["fixtures.api", "fixtures.cleanup"]

expect.set_options(timeout=get_settings().timeout_ms)


@pytest.fixture(scope="session")
def base_url() -> str:
    """pytest-playwright opens relative paths against this URL."""
    return get_settings().base_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}}


@pytest.fixture(autouse=True)
def _playwright_timeouts(request: pytest.FixtureRequest) -> None:
    """Shorter default waits than Playwright's 30 seconds, so a broken page fails fast."""
    if "page" in request.fixturenames:
        page = request.getfixturevalue("page")
        page.set_default_timeout(get_settings().timeout_ms)
