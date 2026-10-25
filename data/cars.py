"""Car test data. Names and plates are unique per call; everything else is a valid default."""

from pathlib import Path
from typing import Any

from helpers.data.unique import unique_name, unique_plate

FILES = Path(__file__).parent / "files"
PHOTOS = [FILES / "car-front.jpg", FILES / "car-side.jpg", FILES / "car-back.jpg"]


def car_payload(test_case: str, **changes: Any) -> dict[str, Any]:
    return {
        "make": "AUTO",
        "model": unique_name(test_case, "Car"),
        "year": 2022,
        "category": "suv",
        "transmission": "automatic",
        "fuel_type": "diesel",
        "seats": 5,
        "doors": 5,
        "mileage_km": 25_000,
        "color": "Grey",
        "license_plate": unique_plate(),
        "daily_price": 50.0,
        "deposit": 200.0,
        "city": "Prishtina",
        "features": ["air_conditioning"],
        **changes,
    }
