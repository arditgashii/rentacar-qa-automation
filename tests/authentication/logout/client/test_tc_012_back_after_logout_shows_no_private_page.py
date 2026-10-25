import allure
import pytest
from playwright.sync_api import Page, expect

from helpers.auth.login import login_as


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.security
@pytest.mark.client
def test_tc_012_back_after_logout_shows_no_private_page(page: Page) -> None:
    """TC-012 After logout, the browser Back button does not show a private page again."""
    with allure.step("log in as a client and open My listings"):
        login_as(page, "client")
        page.goto("/my/listings")
        expect(page.get_by_test_id("nav-my-listings"), "My listings did not open").to_be_visible()

    with allure.step("log out"):
        page.get_by_test_id("nav-logout").click()
        expect(page.get_by_test_id("flash-success")).to_have_text("You are logged out.")

    with allure.step("press Back"):
        page.go_back()

    with allure.step("the private page is not shown again; the visitor is asked to log in"):
        expect(page, "Back after logout should lead to the login page").to_have_url(
            "/login?next=%2Fmy%2Flistings"
        )
        expect(page.get_by_test_id("nav-logout"), "the page still looks logged in").to_have_count(0)
