"""Logged-in API clients for this worker's accounts."""

from collections.abc import Iterator

import pytest

from config.settings import lease_account
from helpers.api.client import ApiClient, api_login


@pytest.fixture
def anonymous_api() -> Iterator[ApiClient]:
    client = ApiClient()
    yield client
    client.close()


@pytest.fixture
def admin_api() -> Iterator[ApiClient]:
    client = api_login(lease_account("admin"))
    yield client
    client.close()


@pytest.fixture
def client_api() -> Iterator[ApiClient]:
    """The worker's first client."""
    client = api_login(lease_account("client", 0))
    yield client
    client.close()


@pytest.fixture
def second_client_api() -> Iterator[ApiClient]:
    """The worker's second client, for tests that need two different people."""
    client = api_login(lease_account("client", 1))
    yield client
    client.close()
