"""A thin httpx client for the DriveNow REST API with readable failures."""

from typing import Any

import httpx

from config.settings import Account, get_settings


class ApiError(AssertionError):
    """An unexpected status code. The message shows the request and the response body."""


class ApiClient:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._http = httpx.Client(base_url=settings.api_url, headers=headers, timeout=30)

    def close(self) -> None:
        self._http.close()

    def request(self, method: str, path: str, expected: int | None = None, **kwargs: Any) -> httpx.Response:
        """Sends a request. With `expected`, any other status raises ApiError."""
        response = self._http.request(method, path, **kwargs)
        if expected is not None and response.status_code != expected:
            raise ApiError(
                f"{method} {path} returned {response.status_code}, expected {expected}: {response.text[:500]}"
            )
        return response

    def get(self, path: str, expected: int | None = 200, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, expected, **kwargs)

    def post(self, path: str, expected: int | None = 200, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, expected, **kwargs)

    def put(self, path: str, expected: int | None = 200, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, expected, **kwargs)

    def patch(self, path: str, expected: int | None = 200, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, expected, **kwargs)

    def delete(self, path: str, expected: int | None = 204, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, expected, **kwargs)


def api_login(account: Account) -> ApiClient:
    """An ApiClient logged in as the account."""
    anonymous = ApiClient()
    try:
        response = anonymous.post("/auth/login", json={"email": account.email, "password": account.password})
    finally:
        anonymous.close()
    return ApiClient(response.json()["access_token"])
