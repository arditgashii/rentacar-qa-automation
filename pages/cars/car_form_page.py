from pathlib import Path
from typing import Any, Self

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class CarFormPage(BasePage):
    """The "List your car" form (/cars/new) and the edit form (/cars/{id}/edit) with its photo panel."""

    path = "/cars/new"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.form = self.by_id("car-form")
        self.photos_input = self.by_id("car-form-photos")
        self.submit = self.by_id("car-form-submit")
        self.photo_manager = self.by_id("photo-manager")

    def open_edit(self, car_id: int) -> Self:
        self.page.goto(f"/cars/{car_id}/edit")
        return self

    def field(self, name: str) -> Locator:
        return self.by_id(f"car-form-{name.replace('_', '-')}")

    def feature(self, value: str) -> Locator:
        return self.by_id(f"car-form-feature-{value}")

    def fill(self, values: dict[str, Any]) -> None:
        """Fills text fields and selects; `features` is a list of features that must end up checked."""
        for name, value in values.items():
            if name == "features":
                for checkbox in self.form.locator("[data-testid^=car-form-feature-]").all():
                    checkbox.set_checked(checkbox.get_attribute("value") in value)
            elif self.field(name).evaluate("el => el.tagName") == "SELECT":
                self.field(name).select_option(str(value))
            else:
                self.field(name).fill(str(value))

    def attach_photos(self, paths: list[Path]) -> None:
        self.photos_input.set_input_files([str(p) for p in paths])

    def save(self) -> None:
        self.submit.click()

    def photo_items(self) -> Locator:
        return self.photo_manager.locator("[data-testid^=photo-item-]")

    def main_photo_badge(self, index: int) -> Locator:
        """The "Main photo" badge of the photo at this position (it exists on one photo only)."""
        return self.photo_items().nth(index).get_by_test_id("photo-primary-badge")
