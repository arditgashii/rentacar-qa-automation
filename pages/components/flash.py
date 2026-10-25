from playwright.sync_api import Page, expect


class Flash:
    """The message shown at the top of the page after an action."""

    def __init__(self, page: Page) -> None:
        self.success = page.get_by_test_id("flash-success")
        self.error = page.get_by_test_id("flash-error")

    def expect_success(self, text: str) -> None:
        expect(self.success, "no success message after the action").to_contain_text(text)

    def expect_error(self, text: str) -> None:
        expect(self.error, "no error message after the action").to_contain_text(text)
