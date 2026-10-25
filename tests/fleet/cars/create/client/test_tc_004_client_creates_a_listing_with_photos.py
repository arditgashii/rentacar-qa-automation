import re

import allure
import pytest
from playwright.sync_api import Page, expect

from data.cars import PHOTOS, car_payload
from fixtures.cleanup import Cleanup
from helpers.api.client import ApiClient
from helpers.auth.login import login_as
from helpers.azure.blob import blob_name_from_url, blob_properties, blob_storage_configured
from helpers.cars.api import get_car_via_api
from pages.cars.car_form_page import CarFormPage
from pages.components.flash import Flash

FORM_FIELDS = [
    "make", "model", "year", "color", "category", "transmission", "fuel_type",
    "seats", "doors", "mileage_km", "license_plate", "daily_price", "deposit", "city",
]  # fmt: skip


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.integration
@pytest.mark.client
def test_tc_004_client_creates_a_listing_with_photos(
    page: Page, client_api: ApiClient, cleanup: Cleanup
) -> None:
    """TC-004 Client creates a listing with 3 photos; the photos are in Blob Storage and the first is primary."""
    form = CarFormPage(page)
    car = car_payload("TC-004", daily_price="47.50", features=["gps", "bluetooth"])

    with allure.step("log in as a client and open List your car"):
        login_as(page, "client")
        form.open()

    with allure.step("fill every field, attach 3 photos and publish"):
        form.fill({name: car[name] for name in FORM_FIELDS} | {"features": car["features"]})
        form.attach_photos(PHOTOS)
        form.save()
        Flash(page).expect_success("Car published.")
        expect(page, "the edit page of the new car should open").to_have_url(re.compile(r"/cars/\d+/edit$"))
        car_id = int(page.url.split("/")[-2])
        cleanup.car(car_id)

    with allure.step("the edit page shows the 3 photos, the first one as main photo"):
        expect(form.photo_items(), "wrong number of photos on the edit page").to_have_count(3)
        expect(form.main_photo_badge(0), "the first photo should be the main photo").to_be_visible()

    with allure.step("the API has the car with the entered values and 3 photos, the first one primary"):
        saved = get_car_via_api(client_api, car_id)
        assert saved["model"] == car["model"], f"model: expected {car['model']}, got {saved['model']}"
        assert saved["daily_price"] == 47.5, f"daily_price: expected 47.50, got {saved['daily_price']}"
        assert sorted(saved["features"]) == ["bluetooth", "gps"], f"features: got {saved['features']}"
        primary_flags = [photo["is_primary"] for photo in saved["photos"]]
        assert primary_flags == [True, False, False], f"main photo flags: got {primary_flags}"

    with allure.step("every photo is served and stored in Blob Storage"):
        for photo in saved["photos"]:
            response = page.request.get(photo["url"])
            assert response.ok, f"{photo['url']} returned {response.status}"
            assert response.headers["content-type"] == "image/jpeg", f"{photo['url']} is not a JPEG"
            if blob_storage_configured():
                stored = blob_properties(blob_name_from_url(photo["url"]))
                assert stored, f"{photo['url']} is not in Blob Storage"
                assert stored["size"] == photo["size_bytes"], f"blob size differs for {photo['url']}"
