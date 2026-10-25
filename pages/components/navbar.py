from playwright.sync_api import Page


class Navbar:
    """The top bar. Links differ by role: admins see Dashboard, clients see My listings."""

    def __init__(self, page: Page) -> None:
        self.root = page.get_by_test_id("navbar")
        self.user_name = page.get_by_test_id("nav-user-name")
        self.login = page.get_by_test_id("nav-login")
        self.logout = page.get_by_test_id("nav-logout")
        self.admin_dashboard = page.get_by_test_id("nav-admin")
        self.admin_cars = page.get_by_test_id("nav-admin-cars")
        self.my_listings = page.get_by_test_id("nav-my-listings")
