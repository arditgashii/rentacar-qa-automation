from playwright.sync_api import Page

from config.settings import Account, Role, lease_account
from pages.authentication.login_page import LoginPage
from pages.components.flash import Flash


def login_as(page: Page, role: Role, slot: int = 0) -> Account:
    """Logs the browser in with this worker's account for the role and returns the account."""
    account = lease_account(role, slot)
    LoginPage(page).open().log_in(account.email, account.password)
    Flash(page).expect_success("Welcome back")
    return account
