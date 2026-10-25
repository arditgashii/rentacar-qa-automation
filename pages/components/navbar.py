from playwright.sync_api import Page


class Navbar:
    """The top bar. Its links differ by role; only admins see Dashboard."""

    def __init__(self, page: Page) -> None:
        self.admin_dashboard = page.get_by_test_id("nav-admin")
