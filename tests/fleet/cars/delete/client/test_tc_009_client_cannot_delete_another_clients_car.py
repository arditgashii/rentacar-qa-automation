import allure
import pytest

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.cars.api import car_exists, create_car_via_api


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.security
@pytest.mark.client
@pytest.mark.known_bug("BUG-003")
def test_tc_009_client_cannot_delete_another_clients_car(
    client_api: ApiClient, second_client_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-009 A client cannot delete another client's car (403 and the car still exists)."""
    owner, stranger = client_api, second_client_api

    with allure.step("a client lists a car"):
        car = create_car_via_api(owner, "TC-009")
        cleanup.car(car["id"])

    with allure.step("another client sends DELETE for that car"):
        response = stranger.delete(f"/cars/{car['id']}", expected=None)

    with allure.step("the request is refused and the car is still there"):
        still_there = car_exists(owner, car["id"])
        outcome = f"got {response.status_code} and the car was {'kept' if still_there else 'deleted'}"
        assert response.status_code == 403, f"another client could delete the car: expected 403, {outcome}"
        assert still_there, f"the car was deleted although the request was refused: {outcome}"
