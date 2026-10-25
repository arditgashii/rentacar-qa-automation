import allure
import pytest

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.azure.servicebus import find_booking_event, service_bus_configured
from helpers.bookings.api import book_car_via_api, days_from_today, notifications_for_booking
from helpers.cars.api import create_car_via_api
from helpers.data.wait import wait_until


@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.integration
@pytest.mark.client
def test_tc_007_client_books_a_car(
    client_api: ApiClient, second_client_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-007 Client books a car: the total is right, the booking is pending, the event reaches Service Bus and both people are notified."""
    owner, renter = client_api, second_client_api

    with allure.step("the owner lists a car at 45.50 per day"):
        car = create_car_via_api(owner, "TC-007", daily_price=45.50)
        cleanup.car(car["id"])

    with allure.step("another client books it for 3 days"):
        response = book_car_via_api(renter, car["id"], days_from_today(5), days_from_today(8))
        assert response.status_code == 201, f"booking refused: {response.status_code} {response.text}"
        booking = response.json()

    with allure.step("the booking is pending and costs 3 x 45.50"):
        assert booking["status"] == "pending", f"status: expected pending, got {booking['status']}"
        assert booking["days"] == 3, f"days: expected 3, got {booking['days']}"
        assert booking["total_price"] == 136.50, f"total: expected 136.50, got {booking['total_price']}"

    if service_bus_configured():
        with allure.step("a booking.created event was published on Service Bus"):
            event = wait_until(
                lambda: find_booking_event(booking["id"], "booking.created"),
                timeout=15,
                message=f"no booking.created event for booking {booking['id']} on the audit subscription",
            )
            assert event["total_price"] == "136.50", f"event total: got {event['total_price']}"
            assert event["owner_id"] == car["owner_id"], "the event names the wrong owner"

    with allure.step("the owner and the renter are both notified"):
        for person, api in (("owner", owner), ("renter", renter)):
            wait_until(
                lambda api=api: notifications_for_booking(api, booking["id"]),
                timeout=15,
                message=f"the {person} got no notification for booking {booking['id']}",
            )
