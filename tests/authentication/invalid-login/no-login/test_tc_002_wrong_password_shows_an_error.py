import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import lease_account
from pages.authentication.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.no_login
def test_tc_002_wrong_password_shows_an_error(page: Page) -> None:
    """TC-002 Login with a wrong password shows an error and no session."""
    login = LoginPage(page)
    account = lease_account("client")

    with allure.step("submit a real email with a wrong password"):
        login.open().log_in(account.email, "not-the-password")

    with allure.step("the form stays open with a clear error"):
        expect(login.error, "no error message for a wrong password").to_have_text("Wrong email or password.")
        expect(page, "a failed login must stay on the login page").to_have_url("/login")
        expect(login.email, "the email should be kept for the next try").to_have_value(account.email)

    with allure.step("no session was created"):
        cookies = {cookie["name"] for cookie in page.context.cookies()}
        assert "access_token" not in cookies, "a session cookie was set although the login failed"
        page.goto("/my/listings")
        expect(page, "a private page must send the visitor to the login").to_have_url(
            "/login?next=%2Fmy%2Flistings"
        )
