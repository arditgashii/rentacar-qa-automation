from playwright.sync_api import Locator, Page

from pages.base_page import BasePage
from pages.components.confirm_dialog import ConfirmDialog


class AdminCarsPage(BasePage):
    """Admin > Cars: every car of every owner, with search and delete."""

    path = "/admin/cars"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = self.by_id("admin-cars-search")
        self.apply = self.by_id("admin-cars-apply")
        self.empty = self.by_id("admin-cars-empty")

    def search(self, text: str) -> None:
        self.search_input.fill(text)
        self.apply.click()

    def row(self, car_id: int) -> Locator:
        return self.by_id(f"admin-cars-row-{car_id}")

    def delete(self, car_id: int) -> None:
        self.by_id(f"admin-cars-delete-{car_id}").click()
        ConfirmDialog(self.page).accept("Delete")
