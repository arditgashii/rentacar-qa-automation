from typing import Any

from helpers.api.client import ApiClient


def register_via_api(api: ApiClient, email: str, password: str, full_name: str) -> dict[str, Any]:
    payload = {"email": email, "password": password, "full_name": full_name}
    return api.post("/auth/register", json=payload, expected=201).json()


def deactivate_user_via_api(admin: ApiClient, user_id: int) -> None:
    """The platform has no user delete, so cleanup deactivates the account instead."""
    response = admin.patch(f"/admin/users/{user_id}", json={"is_active": False}, expected=None)
    if response.status_code not in (200, 404):
        raise AssertionError(f"cleanup could not deactivate user {user_id}: {response.text}")
