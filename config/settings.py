"""Where the platform runs, which accounts the tests use, and the optional Azure connections.

Everything has a default that matches the seeded DriveNow stack on localhost, so the suite runs
without a .env file. Override any value in .env or in the environment (see .env.example).
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Role = Literal["admin", "client"]


@dataclass(frozen=True)
class Account:
    email: str
    password: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    base_url: str = "http://localhost:8000"
    test_password: str = "DriveNow!2026"

    # Comma separated pools. Each xdist worker leases its own accounts, so workers never share data.
    pool_admin: str = "admin1@drivenow.test,admin2@drivenow.test,admin3@drivenow.test"
    pool_client: str = Field(
        default=",".join(f"client{n}@drivenow.test" for n in range(1, 7)),
        description="Two clients per worker: worker 1 gets client 1 and 2, worker 2 gets 3 and 4.",
    )
    inactive_email: str = "inactive@drivenow.test"

    # Optional: when set, integration tests also look inside Azure (Azurite and the Service Bus emulator).
    azure_storage_connection_string: str = ""
    photo_container: str = "car-photos"
    servicebus_connection_string: str = ""
    booking_topic: str = "booking-events"
    audit_subscription: str = "audit"

    keep_data: bool = False
    timeout_ms: int = 10_000

    @property
    def api_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1"

    def pool(self, role: Role) -> list[str]:
        raw = self.pool_admin if role == "admin" else self.pool_client
        return [email.strip() for email in raw.split(",") if email.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def worker_index() -> int:
    """0 for the main process and for xdist worker gw0, 1 for gw1, and so on."""
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    return int(worker.removeprefix("gw") or 0)


def lease_account(role: Role, slot: int = 0) -> Account:
    """The account this worker uses for a role. `slot` picks the second client of the worker (0 or 1)."""
    settings = get_settings()
    pool = settings.pool(role)
    per_worker = 2 if role == "client" else 1
    if slot >= per_worker:
        raise ValueError(f"A worker has {per_worker} {role} account(s); slot {slot} does not exist.")
    position = worker_index() * per_worker + slot
    if position >= len(pool):
        workers = len(pool) // per_worker
        raise RuntimeError(
            f"Worker {worker_index() + 1} needs {role} account {position + 1}, but the pool has {len(pool)}. "
            f"Add accounts to POOL_{role.upper()} or run with at most -n {workers}."
        )
    return Account(pool[position], settings.test_password)
