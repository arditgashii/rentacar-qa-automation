import allure
import pytest
from playwright.sync_api import Page, expect

from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.auth.login import login_as
from helpers.cars.api import create_car_via_api
from pages.admin.admin_cars_page import AdminCarsPage
from pages.components.flash import Flash


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.admin
def test_tc_010_admin_deletes_a_car(page: Page, client_api: ApiClient, cleanup: Cleanup) -> None:
    """TC-010 Admin deletes a car; it disappears from the list and the API returns 404."""
    cars = AdminCarsPage(page)

    with allure.step("a client has a car listed"):
        car = create_car_via_api(client_api, "TC-010")
        cleanup.car(car["id"])

    with allure.step("an admin finds it in Admin > Cars"):
        login_as(page, "admin")
        cars.open().search(car["model"])
        expect(cars.row(car["id"]), "the car is not in the admin list").to_be_visible()

    with allure.step("delete it and confirm"):
        cars.delete(car["id"])
        Flash(page).expect_success("Car deleted.")

    with allure.step("the car is gone from the list and from the API"):
        cars.search(car["model"])
        expect(cars.row(car["id"]), "the deleted car is still listed").to_have_count(0)
        expect(cars.empty).to_be_visible()
        status = client_api.get(f"/cars/{car['id']}", expected=None).status_code
        assert status == 404, f"GET the deleted car: expected 404, got {status}"
