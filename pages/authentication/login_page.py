from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    """The login form. It only fills and submits; tests decide what the outcome should be."""

    path = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.email = self.by_id("login-email")
        self.password = self.by_id("login-password")
        self.submit = self.by_id("login-submit")
        self.error = self.by_id("login-error")

    def log_in(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()
