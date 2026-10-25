from typing import Self

from playwright.sync_api import Locator, Page


class BasePage:
    """Shared plumbing for page objects: a page and a shortcut for data-testid locators."""

    path = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def by_id(self, test_id: str) -> Locator:
        return self.page.get_by_test_id(test_id)

    def open(self) -> Self:
        self.page.goto(self.path)
        return self
