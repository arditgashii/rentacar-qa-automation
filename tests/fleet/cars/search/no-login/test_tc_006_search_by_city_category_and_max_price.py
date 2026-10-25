import allure
import pytest

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.cars.api import create_car_via_api, search_cars_via_api
from helpers.data.unique import unique_city


@pytest.mark.regression
@pytest.mark.api
@pytest.mark.no_login
@pytest.mark.known_bug("BUG-004")
def test_tc_006_search_by_city_category_and_max_price(
    client_api: ApiClient, anonymous_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-006 Search by city, category and max price returns exactly the matching cars, the boundary price included."""
    city = unique_city("TC-006")
    max_price = 75.50

    with allure.step("four cars in a city nobody else uses"):
        cars = {
            "cheaper SUV": create_car_via_api(client_api, "TC-006", city=city, category="suv", daily_price=50.0),
            "SUV at exactly the max price": create_car_via_api(client_api, "TC-006", city=city, category="suv", daily_price=max_price),
            "SUV one cent above": create_car_via_api(client_api, "TC-006", city=city, category="suv", daily_price=75.51),
            "economy car": create_car_via_api(client_api, "TC-006", city=city, category="economy", daily_price=40.0),
        }  # fmt: skip
        for car in cars.values():
            cleanup.car(car["id"])

    with allure.step(f"a visitor searches SUVs in that city up to {max_price}"):
        found = search_cars_via_api(anonymous_api, city=city, category="suv", max_price=max_price)

    with allure.step("exactly the cheaper SUV and the one at the max price come back"):
        expected = {name for name in ("cheaper SUV", "SUV at exactly the max price")}
        names = {car["id"]: name for name, car in cars.items()}
        actual = {names.get(car["id"], f"unknown car {car['id']}") for car in found}
        assert actual == expected, (
            f"search results: expected {sorted(expected)}, got {sorted(actual)}. "
            f"Missing: {sorted(expected - actual)}; unexpected: {sorted(actual - expected)}"
        )
