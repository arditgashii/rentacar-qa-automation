import allure
import pytest

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.bookings.api import book_car_via_api, days_from_today
from helpers.cars.api import create_car_via_api


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.client
@pytest.mark.known_bug("BUG-002")
def test_tc_008_overlapping_booking_is_refused(
    client_api: ApiClient, second_client_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-008 An overlapping booking (starts before and ends after an existing one) is refused with 409."""
    owner, renter = client_api, second_client_api

    with allure.step("a car is booked from day 10 to day 12"):
        car = create_car_via_api(owner, "TC-008")
        cleanup.car(car["id"])
        first = book_car_via_api(renter, car["id"], days_from_today(10), days_from_today(12))
        assert first.status_code == 201, f"the first booking was refused: {first.text}"

    with allure.step("a second booking from day 9 to day 14 covers the whole first one"):
        second = book_car_via_api(renter, car["id"], days_from_today(9), days_from_today(14))

    with allure.step("the second booking is refused because the dates are taken"):
        assert second.status_code == 409, (
            f"an overlapping booking was accepted: expected 409 DATES_TAKEN, got {second.status_code} "
            f"(day 9 to 14 covers the existing booking from day 10 to 12, so the car would be double booked)"
        )
        assert second.json()["code"] == "DATES_TAKEN", f"error code: got {second.json()['code']}"
