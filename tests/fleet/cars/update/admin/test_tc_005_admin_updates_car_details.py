import allure
import pytest
from playwright.sync_api import Page

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.auth.login import login_as
from helpers.cars.api import create_car_via_api, get_car_via_api
from pages.cars.car_form_page import CarFormPage
from pages.components.flash import Flash


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.admin
@pytest.mark.known_bug("BUG-001")
def test_tc_005_admin_updates_car_details(page: Page, client_api: ApiClient, cleanup: Cleanup) -> None:
    """TC-005 Admin updates car details (price 89.99, mileage, features) and the saved car has the new values."""
    form = CarFormPage(page)
    changes = {"daily_price": 89.99, "mileage_km": 31_250, "features": ["gps", "heated_seats"]}

    with allure.step("a client has a car listed at 50.00 per day"):
        car = create_car_via_api(client_api, "TC-005", daily_price=50.0, mileage_km=30_000)
        cleanup.car(car["id"])

    with allure.step("an admin opens the car in the edit form"):
        login_as(page, "admin")
        form.open_edit(car["id"])

    with allure.step("change the price, the mileage and the features, then save"):
        form.fill(changes)
        form.save()
        Flash(page).expect_success("Changes saved.")

    with allure.step("the saved car has exactly the new values"):
        saved = get_car_via_api(client_api, car["id"])
        actual = {
            "daily_price": saved["daily_price"],
            "mileage_km": saved["mileage_km"],
            "features": sorted(saved["features"]),
        }
        expected = {**changes, "features": sorted(changes["features"])}
        differences = [
            f"{key}: expected {expected[key]}, got {actual[key]}"
            for key in expected
            if actual[key] != expected[key]
        ]
        assert not differences, "saved car differs from what the admin entered: " + "; ".join(differences)
