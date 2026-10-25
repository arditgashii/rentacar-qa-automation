"""Setup, checks and cleanup of cars through the API."""

from pathlib import Path
from typing import Any

from data.cars import car_payload
from helpers.api.client import ApiClient


def create_car_via_api(api: ApiClient, test_case: str, **changes: Any) -> dict[str, Any]:
    return api.post("/cars", json=car_payload(test_case, **changes), expected=201).json()


def get_car_via_api(api: ApiClient, car_id: int) -> dict[str, Any]:
    return api.get(f"/cars/{car_id}").json()


def car_exists(api: ApiClient, car_id: int) -> bool:
    return api.get(f"/cars/{car_id}", expected=None).status_code == 200


def upload_photo_via_api(api: ApiClient, car_id: int, path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        files = {"file": (path.name, file, "image/jpeg")}
        return api.post(f"/cars/{car_id}/photos", files=files, expected=201).json()


def search_cars_via_api(api: ApiClient, **filters: Any) -> list[dict[str, Any]]:
    return api.get("/cars", params={"page_size": 50, **filters}).json()["items"]


def delete_car_via_api(api: ApiClient, car_id: int) -> None:
    """Deletes a car; a car that is already gone counts as deleted."""
    response = api.delete(f"/cars/{car_id}", expected=None)
    if response.status_code not in (204, 404):
        raise AssertionError(f"cleanup could not delete car {car_id}: {response.status_code} {response.text}")
