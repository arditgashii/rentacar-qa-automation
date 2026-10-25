from playwright.sync_api import Page

from pages.base_page import BasePage


class AdminDashboardPage(BasePage):
    path = "/admin"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.stats = self.by_id("admin-stats")
        self.cars = self.by_id("stat-cars")
        self.active_bookings = self.by_id("stat-active-bookings")
        self.revenue = self.by_id("stat-revenue")
        self.users = self.by_id("stat-users")
        self.bookings_table = self.by_id("bookings-table")
